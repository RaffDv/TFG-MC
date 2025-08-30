# Script: bronze_auto.py
# VERSÃO COM LEITURA AUTOMÁTICA DE INVENTÁRIO
# Uso no Minecraft: \bronze_auto.py <lingotes>
# Exemplo: \bronze_auto.py 12

import sys
import math
from collections import defaultdict
import minescript

# --- CONFIGURAÇÃO ---
# ... (toda a configuração e as funções de cálculo [solve_for_metal, combine_solutions, etc.] permanecem EXATAMENTE IGUAIS ao script anterior) ...
# Apenas cole o miolo do script anterior aqui.
# A única parte que vamos mudar é o bloco final de execução.

# --- FUNÇÕES NÚCLEO (COPIADAS DO SCRIPT ANTERIOR) ---
INGOT_MB_VALUE = 144
ALLOY_RECIPES = { "bronze": { "ideal_components": {"copper": 0.75, "tin": 0.25}, "rules": {"tin": (0.20, 0.30)} } }
DUST_DATA = {
	"copper": {
		"copper_dust": 144,
		"tetrahedrite_dust": 129,
		"small_pile_tetrahedrite_dust": 31
	},
	"tin": {
		"tin_dust": 144,
		"cassiterite_dust": 144,
		"cassiterite_sand_dust": 121,
		"small_tin_dust": 36
	}
}

def solve_for_metal(target_mb, inventory, dust_data_for_metal):
    # ... (código idêntico ao script anterior)
    available_inventory = inventory.copy()
    solution = defaultdict(int)
    current_mb = 0
    sorted_dusts = sorted(dust_data_for_metal.items(), key=lambda item: item[1], reverse=True)
    for dust_name, dust_mb in sorted_dusts:
        if dust_mb <= 0: continue
        if available_inventory.get(dust_name, 0) > 0:
            needed = math.floor((target_mb - current_mb) / dust_mb)
            to_use = min(needed, available_inventory.get(dust_name, 0))
            if to_use > 0:
                solution[dust_name] += to_use
                current_mb += to_use * dust_mb
                available_inventory[dust_name] -= to_use
    if current_mb < target_mb:
        remaining_mb = target_mb - current_mb
        best_option, min_excess = None, float('inf')
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
    # ... (código idêntico ao script anterior)
    combined = sol1.copy()
    for k, v in sol2.items():
        combined[k] = combined.get(k, 0) + v
    return combined

def run_optimizer(ingots_to_produce, inventory):
    # ... (código idêntico ao script anterior, com os minescript.echo)
    try:
        recipe = ALLOY_RECIPES["bronze"]
        total_ideal_mb = ingots_to_produce * INGOT_MB_VALUE
        copper_target = total_ideal_mb * recipe["ideal_components"]["copper"]
        copper_inv = {k: v for k, v in inventory.items() if k in DUST_DATA["copper"]}
        copper_sol, copper_mb, copper_inv_rem = solve_for_metal(copper_target, copper_inv, DUST_DATA["copper"])
        tin_target = total_ideal_mb * recipe["ideal_components"]["tin"]
        tin_inv = {k: v for k, v in inventory.items() if k in DUST_DATA["tin"]}
        tin_sol, tin_mb, tin_inv_rem = solve_for_metal(tin_target, tin_inv, DUST_DATA["tin"])
        final_total_mb = copper_mb + tin_mb
        if final_total_mb > 0:
            current_tin_ratio = tin_mb / final_total_mb
            min_tin, max_tin = recipe["rules"]["tin"]
            if current_tin_ratio > max_tin:
                minescript.echo("§eAVISO: Proporção de Estanho alta ({:.1f}%). Adicionando Cobre...".format(current_tin_ratio * 100))
                needed_copper_mb = (tin_mb / max_tin) - tin_mb
                if needed_copper_mb > copper_mb:
                    additional_copper_needed = needed_copper_mb - copper_mb
                    copper_adjust_sol, copper_adjust_mb, _ = solve_for_metal(additional_copper_needed, copper_inv_rem, DUST_DATA["copper"])
                    copper_sol = combine_solutions(copper_sol, copper_adjust_sol)
                    copper_mb += copper_adjust_mb
            elif current_tin_ratio < min_tin:
                minescript.echo("§eAVISO: Proporção de Estanho baixa ({:.1f}%). Adicionando Estanho...".format(current_tin_ratio * 100))
                needed_tin_mb = (copper_mb * min_tin) / (1 - min_tin)
                if needed_tin_mb > tin_mb:
                    additional_tin_needed = needed_tin_mb - tin_mb
                    tin_adjust_sol, tin_adjust_mb, _ = solve_for_metal(additional_tin_needed, tin_inv_rem, DUST_DATA["tin"])
                    tin_sol = combine_solutions(tin_sol, tin_adjust_sol)
                    tin_mb += tin_adjust_mb
        minescript.echo("§a" + "=" * 35)
        minescript.echo(f"§aPLANO PARA ~{ingots_to_produce} LINGOTES DE BRONZE")
        minescript.echo("§a" + "=" * 35)
        minescript.echo(f"\n§b--- Cobre (Total: {copper_mb:.0f} mB) ---")
        if not copper_sol: minescript.echo("  §7Nenhum pó de Cobre necessário.")
        else:
            for dust, qty in copper_sol.items(): minescript.echo(f"  §7- {qty}x {dust}")
        minescript.echo(f"\n§6--- Estanho (Total: {tin_mb:.0f} mB) ---")
        if not tin_sol: minescript.echo("  §7Nenhum pó de Estanho necessário.")
        else:
            for dust, qty in tin_sol.items(): minescript.echo(f"  §7- {qty}x {dust}")
        final_total_mb = copper_mb + tin_mb
        final_copper_ratio = (copper_mb / final_total_mb * 100) if final_total_mb > 0 else 0
        final_tin_ratio = (tin_mb / final_total_mb * 100) if final_total_mb > 0 else 0
        minescript.echo("\n§d--- Resumo da Liga ---")
        minescript.echo(f"Total de mB na mistura: {final_total_mb:.0f}")
        minescript.echo(f"Proporção: §b{final_copper_ratio:.1f}% Cobre §f/ §6{final_tin_ratio:.1f}% Estanho")
        minescript.echo(f"Lingotes produzidos: §a{math.floor(final_total_mb / INGOT_MB_VALUE)}")
    except (ValueError, ZeroDivisionError, IndexError) as e:
        minescript.echo(f"§cERRO: Entrada inválida ou erro de cálculo. Verifique seu comando. ({e})")
    except Exception as e:
        minescript.echo(f"§cOcorreu um erro inesperado: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        minescript.echo("§cUso: \\alloy.py <lingotes>")
        minescript.echo("§cExemplo: \\alloy.py 12")
    else:
        try:
            ingots_to_produce = int(sys.argv[1])
            
            minescript.echo("§fEscaneando seu inventário em busca de pós...")
            
            inventory = defaultdict(int)
            all_known_dusts = list(DUST_DATA["copper"].keys()) + list(DUST_DATA["tin"].keys())
            
            # CORREÇÃO: Obter o jogador e depois acessar seu inventário
            player = minescript.player()
            player_inventory = minescript.player_inventory()
            
            for item in player_inventory:
                # O item pode ser nulo se o slot do inventário estiver vazio
                if item is None:
                    continue


                
                if item.item in all_known_dusts:
                    inventory[item.item] += item.count

            if not inventory:
                minescript.echo("§cERRO: Nenhum pó de Cobre ou Estanho encontrado no seu inventário.")
            else:
                minescript.echo(f"§aPós encontrados: {dict(inventory)}")
                run_optimizer(ingots_to_produce, dict(inventory))

        except ValueError:
            minescript.echo("§cERRO: A quantidade de lingotes deve ser um número.")
        except Exception as e:
            minescript.echo(f"§cOcorreu um erro inesperado: {e}")
