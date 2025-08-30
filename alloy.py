import sys
import math
from collections import defaultdict
import minescript


INGOT_MB_VALUE = 144

RECIPES = {
    "copper": {"ideal_components": {"copper": 1}},
    "tin": {
        "ideal_components": {"tin": 1},
    },
    "bronze": {
        "ideal_components": {"copper": 0.75, "tin": 0.25},
        "rules": {"tin": (0.20, 0.30)},
    },
}

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
}


def solve_for_metal(target_mb, inventory, dust_data_for_metal):
    available_inventory = inventory.copy()
    solution = defaultdict(int)
    current_mb = 0
    sorted_dusts = sorted(
        dust_data_for_metal.items(), key=lambda item: item[1], reverse=True
    )
    for dust_name, dust_mb in sorted_dusts:
        if dust_mb <= 0:
            continue
        if available_inventory.get(dust_name, 0) > 0:
            needed = math.floor((target_mb - current_mb) / dust_mb)
            to_use = min(needed, available_inventory.get(dust_name, 0))
            if to_use > 0:
                solution[dust_name] += to_use
                current_mb += to_use * dust_mb
                available_inventory[dust_name] -= to_use
    if current_mb < target_mb:
        remaining_mb = target_mb - current_mb
        best_option, min_excess = None, float("inf")
        for dust_name, dust_mb in dust_data_for_metal.items():
            if available_inventory.get(dust_name, 0) > 0 and dust_mb >= remaining_mb:
                excess = dust_mb - remaining_mb
                if excess < min_excess:
                    min_excess, best_option = excess, dust_name
        if best_option:
            solution[best_option] += 1
            current_mb += dust_data_for_metal[best_option]
            available_inventory[best_option] -= 1
    return dict(solution), current_mb, dict(available_inventory)


def combine_solutions(sol1, sol2):
    combined = sol1.copy()
    for k, v in sol2.items():
        combined[k] = combined.get(k, 0) + v
    return combined


def run_optimizer(ingots_to_produce, inventory, metal_required):
    try:
        recipe = RECIPES[metal_required]
        total_ideal_mb = ingots_to_produce * INGOT_MB_VALUE

        solutions = {}
        metal_mbs = {}
        metal_inv_rem = {}

        # Calculate initial metals based on ideal proportions
        for metal, ratio in recipe["ideal_components"].items():
            if metal not in DUST_DATA:
                continue
            target = total_ideal_mb * ratio
            inv = {k: v for k, v in inventory.items() if k in DUST_DATA[metal]}
            sol, mb, inv_rem = solve_for_metal(target, inv, DUST_DATA[metal])
            solutions[metal] = sol
            metal_mbs[metal] = mb
            metal_inv_rem[metal] = inv_rem

        # Apply rules for adjustment (currently specific to bronze)
        if (
            "rules" in recipe
            and "tin" in recipe["rules"]
            and "tin" in metal_mbs
            and "copper" in metal_mbs
        ):
            copper_mb = metal_mbs["copper"]
            tin_mb = metal_mbs["tin"]
            final_total_mb = copper_mb + tin_mb

            if final_total_mb > 0:
                current_tin_ratio = tin_mb / final_total_mb
                min_tin, max_tin = recipe["rules"]["tin"]

                if current_tin_ratio > max_tin:
                    minescript.echo(
                        f"§eAVISO: Proporção de Estanho alta ({current_tin_ratio * 100:.1f}%). Adicionando Cobre..."
                    )
                    # total copper needed = (tin_mb / max_tin) - tin_mb
                    needed_copper_total = (tin_mb / max_tin) - tin_mb
                    if needed_copper_total > copper_mb:
                        additional_copper = needed_copper_total - copper_mb
                        copper_adjust_sol, copper_adjust_mb, _ = solve_for_metal(
                            additional_copper,
                            metal_inv_rem["copper"],
                            DUST_DATA["copper"],
                        )
                        solutions["copper"] = combine_solutions(
                            solutions["copper"], copper_adjust_sol
                        )
                        metal_mbs["copper"] += copper_adjust_mb

                elif current_tin_ratio < min_tin:
                    minescript.echo(
                        f"§eAVISO: Proporção de Estanho baixa ({current_tin_ratio * 100:.1f}%). Adicionando Estanho..."
                    )
                    # total tin needed = (copper_mb * min_tin) / (1 - min_tin)
                    needed_tin_total = (copper_mb * min_tin) / (1 - min_tin)
                    if needed_tin_total > tin_mb:
                        additional_tin = needed_tin_total - tin_mb
                        tin_adjust_sol, tin_adjust_mb, _ = solve_for_metal(
                            additional_tin, metal_inv_rem["tin"], DUST_DATA["tin"]
                        )
                        solutions["tin"] = combine_solutions(
                            solutions["tin"], tin_adjust_sol
                        )
                        metal_mbs["tin"] += tin_adjust_mb

        # --- Output section ---
        minescript.echo("§a" + "=" * 35)
        minescript.echo(
            f"§aPLANO PARA ~{ingots_to_produce} LINGOTES DE {metal_required.upper()}"
        )
        minescript.echo("§a" + "=" * 35)

        summary_proportions = []
        final_total_mb = sum(metal_mbs.values())

        for metal in recipe["ideal_components"]:
            if metal not in metal_mbs:
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
            # This is a bit of a hack for color, but works for the common ones
            color = "b" if metal == "copper" else "6" if metal == "tin" else "f"
            summary_proportions.append(f"§{color}{ratio:.1f}% {metal.capitalize()}")

        minescript.echo("\n§d--- Resumo da Liga ---")
        minescript.echo(f"Total de mB na mistura: {final_total_mb:.0f}")
        minescript.echo("Proporção: " + " §f/ ".join(summary_proportions))
        minescript.echo(
            f"Lingotes produzidos: §a{math.floor(final_total_mb / INGOT_MB_VALUE)}"
        )

    except (ValueError, ZeroDivisionError, IndexError) as e:
        minescript.echo(
            f"§cERRO: Entrada inválida ou erro de cálculo. Verifique seu comando. ({e})"
        )
    except Exception as e:
        minescript.echo(f"§cOcorreu um erro inesperado: {e}")


if __name__ == "__main__":
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

            all_known_dusts = []
            for metal in DUST_DATA:
                all_known_dusts.extend(DUST_DATA[metal].keys())

            player = minescript.player()
            player_inventory = minescript.player_inventory()

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
                run_optimizer(ingots_to_produce, dict(inventory), metal_required)

        except ValueError:
            minescript.echo("§cERRO: A quantidade de lingotes deve ser um número.")
        except Exception as e:
            minescript.echo(f"§cOcorreu um erro inesperado: {e}")
