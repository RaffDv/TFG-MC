import sys
import math
from collections import defaultdict
import minescript


# Valor em mili-baldes (mB) para produzir um único lingote.
INGOT_MB_VALUE = 144

# Define as receitas das ligas, suas proporções ideais e regras de validação.
RECIPES = {
    "copper": {"optimal_ratio": {"copper": 1}},
    "tin": {"optimal_ratio": {"tin": 1}},
    "iron": {"optimal_ratio": {"iron": 1}},
    "bronze": {
        "optimal_ratio": {"copper": 0.75, "tin": 0.25},
        "rules": {"tin": (0.20, 0.30), "copper": (0.70, 0.80)},
    },
    "bismuth_bronze": {
        "optimal_ratio": {"zinc": 0.5, "copper": 0.3, "bismuth": 0.2},
        "rules": {"zinc": (0.4, 0.6), "copper": (0.2, 0.4), "bismuth": (0.1, 0.3)},
    },
    "black_bronze": {
        "optimal_ratio": {"copper": 0.7, "silver": 0.15, "gold": 0.15},
        "rules": {"copper": (0.5, 0.8), "silver": (0.1, 0.2), "gold": (0.1, 0.2)},
    },
    "invar": {
        "optimal_ratio": {"iron": 0.66, "nickel": 0.34},
        "rules": {"iron": (0.60, 0.70), "nickel": (0.30, 0.40)},
    },
}

# Mapeia cada tipo de pó para a quantidade de metal (em mB) que ele produz.
DUST_DATA = {
    "copper": {
        "copper_dust": 144,
        "tetrahedrite_dust": 129,
        "small_pile_tetrahedrite_dust": 31,
    },
    "tin": {
        "tin_dust": 144,
        "cassiterite_dust": 144,
        "cassiterite_sand_dust": 121,
        "small_tin_dust": 36,
    },
    "gold": {"gold_dust": 144, "small_gold_dust": 36},
    "silver": {"silver_dust": 144, "small_silver_dust": 36},
    "bismuth": {"bismuth_dust": 144, "small_bismuth_dust": 36},
    "zinc": {"sphalerite_dust": 129, "small_sphalerite_dust": 36},
    "iron": {
        "hematite_dust": 129,
        "small_hematite_dust": 31,
        "goethite_dust": 129,
        "small_goethite_dust": 31,
        "magnetite_dust": 129,
        "small_magnetite_dust": 31,
        "pyrite_dust": 129,
        "small_pyrite_dust": 31,
        "limonite_dust": 129,
        "small_limonite_dust": 31,
        "iron_dust": 144,
        "small_iron_dust": 36,
        "yellow_limonite_dust": 129,
        "small_yellow_limonite_dust": 31,
    },
    "nickel": {"nickel_dust": 144, "small_nickel_dust": 36},
}


# Função principal que decide quais pós usar para atingir uma meta de metal.
def solve_for_metal(target_mb, inventory, dust_data_for_metal):
    available_inventory = inventory.copy()
    solution = defaultdict(int)
    current_mb = 0
    # Ordena os pós do mais valioso (mais mB) para o menos valioso, para uma abordagem 'gulosa'.
    sorted_dusts = sorted(
        dust_data_for_metal.items(), key=lambda item: item[1], reverse=True
    )
    # Primeira fase: tenta preencher a meta usando a maior quantidade possível dos pós mais valiosos.
    for dust_name, dust_mb in sorted_dusts:
        if dust_mb <= 0:
            continue
        if available_inventory.get(dust_name, 0) > 0:
            # Calcula quantos itens deste pó são necessários para atingir o restante da meta.
            needed = math.floor((target_mb - current_mb) / dust_mb)
            # Usa o mínimo entre o necessário e o que está disponível no inventário.
            to_use = min(needed, available_inventory.get(dust_name, 0))
            if to_use > 0:
                solution[dust_name] += to_use
                current_mb += to_use * dust_mb
                available_inventory[dust_name] -= to_use
    # Segunda fase: se a meta não foi atingida, lida com o valor que falta.
    if current_mb < target_mb:
        remaining_mb = target_mb - current_mb
        best_option, min_excess = None, float("inf")
        # Procura pelo pó que completa a meta causando o menor desperdício (menor excesso de mB).
        for dust_name, dust_mb in dust_data_for_metal.items():
            if available_inventory.get(dust_name, 0) > 0 and dust_mb >= remaining_mb:
                excess = dust_mb - remaining_mb
                if excess < min_excess:
                    min_excess, best_option = excess, dust_name
        # Adiciona uma unidade do pó de 'menor desperdício' para garantir que a meta seja atingida.
        if best_option:
            solution[best_option] += 1
            current_mb += dust_data_for_metal[best_option]
            available_inventory[best_option] -= 1
    return dict(solution), current_mb, dict(available_inventory)


# Função auxiliar para combinar dicionários de soluções.
def combine_solutions(sol1, sol2):
    combined = sol1.copy()
    for k, v in sol2.items():
        combined[k] = combined.get(k, 0) + v
    return combined


# Orquestra todo o processo de otimização da liga.
def run_optimizer(ingots_to_produce, inventory, metal_required):
    try:
        recipe = RECIPES[metal_required]
        # Calcula a quantidade total de metal líquido (mB) necessária para a produção.
        total_ideal_mb = ingots_to_produce * INGOT_MB_VALUE

        solutions = {}
        metal_mbs = {}
        metal_inv_rem = {}

        # Fase 1: Atingir a proporção ótima inicial.
        for metal, ratio in recipe["optimal_ratio"].items():
            if metal not in DUST_DATA:
                continue
            target = total_ideal_mb * ratio
            inv = {k: v for k, v in inventory.items() if k in DUST_DATA.get(metal, {})}
            sol, mb, inv_rem = solve_for_metal(target, inv, DUST_DATA[metal])
            solutions[metal] = sol
            metal_mbs[metal] = mb
            metal_inv_rem[metal] = inv_rem

        # Fase 2: Ajuste iterativo para satisfazer as regras de min/max.
        max_iterations = 10
        for i in range(max_iterations):
            made_adjustment = False
            current_total_mb = sum(metal_mbs.values())
            if current_total_mb == 0:
                break

            rules = recipe.get("rules", {})
            # Checa violações de regras (mínimo primeiro, depois máximo)
            for metal, (min_rule, max_rule) in rules.items():
                if metal not in metal_mbs:
                    continue

                current_ratio = metal_mbs[metal] / current_total_mb
                other_metals_mb = current_total_mb - metal_mbs[metal]

                # Se a proporção atual for menor que o mínimo permitido
                if current_ratio < min_rule:
                    # Calcula o total de metal necessário para atingir a proporção mínima.
                    needed_metal_total = (min_rule * other_metals_mb) / (1 - min_rule)
                    if needed_metal_total > metal_mbs[metal]:
                        additional_metal = needed_metal_total - metal_mbs[metal]
                        minescript.echo(
                            f"§eAjuste: {metal} abaixo do mínimo. Adicionando {additional_metal:.0f} mB..."
                        )
                        adjust_sol, adjust_mb, inv_rem = solve_for_metal(
                            additional_metal, metal_inv_rem[metal], DUST_DATA[metal]
                        )
                        solutions[metal] = combine_solutions(
                            solutions[metal], adjust_sol
                        )
                        metal_mbs[metal] += adjust_mb
                        metal_inv_rem[metal] = inv_rem
                        made_adjustment = True
                        break  # Recomeça o ciclo de ajuste

            if made_adjustment:
                continue  # Vai para a próxima iteração para reavaliar as proporções

            for metal, (min_rule, max_rule) in rules.items():
                if metal not in metal_mbs:
                    continue

                current_ratio = metal_mbs[metal] / current_total_mb

                # Se a proporção atual for maior que o máximo permitido
                if current_ratio > max_rule:
                    # Calcula o novo total da liga para que o metal atual fique na proporção máxima.
                    needed_total_mb = metal_mbs[metal] / max_rule
                    mb_to_add = needed_total_mb - current_total_mb

                    if mb_to_add > 0:
                        minescript.echo(
                            f"§eAjuste: {metal} acima do máximo. Diluindo com outros metais..."
                        )
                        # Distribui a quantidade a ser adicionada entre os outros metais da receita.
                        other_metals_ratio_sum = sum(
                            v for k, v in recipe["optimal_ratio"].items() if k != metal
                        )
                        for other_metal, ratio in recipe["optimal_ratio"].items():
                            if other_metal == metal:
                                continue
                            # Adiciona uma porção proporcional de cada outro metal.
                            metal_to_add = mb_to_add * (ratio / other_metals_ratio_sum)
                            adjust_sol, adjust_mb, inv_rem = solve_for_metal(
                                metal_to_add,
                                metal_inv_rem[other_metal],
                                DUST_DATA[other_metal],
                            )
                            solutions[other_metal] = combine_solutions(
                                solutions[other_metal], adjust_sol
                            )
                            metal_mbs[other_metal] += adjust_mb
                            metal_inv_rem[other_metal] = inv_rem
                        made_adjustment = True
                        break  # Recomeça o ciclo de ajuste

            if not made_adjustment:
                break  # Se nenhuma regra foi violada, o plano está estável.

        # --- Seção de Saída: Formata e exibe o plano para o usuário ---
        minescript.echo("§a" + "=" * 35)
        minescript.echo(
            f"§aPLANO PARA ~{ingots_to_produce} LINGOTES DE {metal_required.upper()}"
        )
        minescript.echo("§a" + "=" * 35)

        summary_proportions = []
        final_total_mb = sum(metal_mbs.values())

        for metal in recipe["optimal_ratio"]:
            if metal not in metal_mbs or metal_mbs[metal] == 0:
                continue

            mb = metal_mbs[metal]
            minescript.echo(f"\n§b--- {metal.capitalize()} (Total: {mb:.0f} mB) ---")
            solution_for_metal = solutions.get(metal, {})

            if not solution_for_metal:
                minescript.echo(f"  §7Nenhum pó de {metal.capitalize()} necessário.")
            else:
                for dust, qty in sorted(solution_for_metal.items()):
                    minescript.echo(f"  §7- {qty}x {dust}")

            ratio = (mb / final_total_mb * 100) if final_total_mb > 0 else 0
            # Hack para colorir os nomes dos metais mais comuns.
            color = "b" if metal == "copper" else "6" if metal == "tin" else "f"
            summary_proportions.append(f"§{color}{ratio:.1f}% {metal.capitalize()}")

        minescript.echo("\n§d--- Resumo da Liga ---")
        minescript.echo(f"Total de mB na mistura: {final_total_mb:.0f}")
        minescript.echo("Proporção: " + " §f/ ".join(summary_proportions))
        # Calcula e exibe a quantidade final de lingotes que serão produzidos.
        minescript.echo(
            f"Lingotes produzidos: §a{math.floor(final_total_mb / INGOT_MB_VALUE)}"
        )

    except (ValueError, ZeroDivisionError, IndexError) as e:
        minescript.echo(
            f"§cERRO: Entrada inválida ou erro de cálculo. Verifique seu comando. ({e})"
        )
    except Exception as e:
        minescript.echo(f"§cOcorreu um erro inesperado: {e}")


# Ponto de entrada do script.
def main():
    # Verifica se o número de argumentos do comando está correto.
    if len(sys.argv) != 3:
        minescript.echo("§cUso: \alloy <receita> <lingotes>")
        minescript.echo("§cExemplo: \alloy bronze 12")
        minescript.echo("§aReceitas disponíveis: §f" + ", ".join(RECIPES.keys()))
    else:
        try:
            metal_required = sys.argv[1].lower()
            ingots_to_produce = int(sys.argv[2])

            if metal_required not in RECIPES:
                minescript.echo(f"§cERRO: Receita '{metal_required}' não é suportada.")
                minescript.echo(
                    "§aReceitas disponíveis: §f" + ", ".join(RECIPES.keys())
                )
                sys.exit(1)

            minescript.echo("§fEscaneando seu inventário em busca de pós...")

            inventory = defaultdict(int)

            # Cria uma lista de todos os pós conhecidos para facilitar a busca.
            all_known_dusts = []
            for metal in DUST_DATA:
                all_known_dusts.extend(DUST_DATA[metal].keys())

            player = minescript.player()
            player_inventory = minescript.player_inventory()

            # Escaneia o inventário do jogador e conta apenas os pós relevantes para as receitas.
            for item in player_inventory:
                if item is None:
                    continue
                if item.item in all_known_dusts:
                    inventory[item.item] += item.count

            if not inventory:
                minescript.echo(
                    f"§cERRO: Nenhum pó relevante encontrado no seu inventário."
                )
            else:
                minescript.echo(f"§aPós encontrados: {dict(inventory)}")

                # Verifica se o jogador possui pós para todos os metais necessários na receita.
                recipe = RECIPES[metal_required]
                required_metals = set(recipe["optimal_ratio"].keys())

                player_metals = set()
                for metal, dusts in DUST_DATA.items():
                    if any(d in inventory for d in dusts.keys()):
                        player_metals.add(metal)

                if not required_metals.issubset(player_metals):
                    missing_metals = required_metals - player_metals
                    minescript.echo(
                        f"§cERRO: Você não possui os pós necessários para a receita '{metal_required}'."
                    )
                    minescript.echo(
                        f"§cMetais faltando: {', '.join(sorted(list(missing_metals)))}"
                    )
                    sys.exit(1)

                # Inicia o otimizador com a receita, a quantidade e o inventário do jogador.
                run_optimizer(ingots_to_produce, dict(inventory), metal_required)

        except ValueError:
            minescript.echo("§cERRO: A quantidade de lingotes deve ser um número.")
        except Exception as e:
            minescript.echo(f"§cOcorreu um erro inesperado: {e}")


if __name__ == "__main__":
    main()
