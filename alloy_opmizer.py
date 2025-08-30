import json
import math
from collections import defaultdict

# --- CONFIGURAÇÃO ---
INGOT_MB_VALUE = 144
# ATUALIZADO: Agora inclui as regras de proporção mínima e máxima!
ALLOY_RECIPES = {
    "bronze": {
        "ideal_components": {"copper": 0.75, "tin": 0.25},
        "rules": {"tin": (0.20, 0.30)} # [min, max] da proporção de estanho
    }
}
DUST_DATA_FILE = "dusts.json"

# --- FUNÇÕES NÚCLEO (sem alterações) ---

def load_dust_data():
    try:
        with open(DUST_DATA_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"ERRO: Arquivo '{DUST_DATA_FILE}' não encontrado!")
        return None
    return None

def get_inventory(dust_data):
    inventory = defaultdict(int)
    print("\n--- Registro de Inventário ---")
    print("Informe a quantidade de cada pó que você possui (0 se não tiver).")
    for metal in ALLOY_RECIPES["bronze"]["ideal_components"]:
        print(f"\n-- Pós de {metal.capitalize()} --")
        for dust_name in dust_data[metal]:
            while True:
                try:
                    qty_str = input(f"  Quantos '{dust_name}' você tem? ")
                    inventory[dust_name] = int(qty_str)
                    break
                except ValueError:
                    print("    Por favor, digite um número válido.")
    return dict(inventory)

def solve_for_metal(target_mb, inventory, dust_data_for_metal):
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
    """Função para mesclar dois dicionários de solução."""
    combined = sol1.copy()
    for k, v in sol2.items():
        combined[k] = combined.get(k, 0) + v
    return combined

# --- FUNÇÃO PRINCIPAL (LÓGICA ATUALIZADA) ---

def run_optimizer():
    dust_data = load_dust_data()
    if not dust_data: return

    print("=== Otimizador de Ligas v2 (com Verificação de Proporção) ===")
    
    try:
        ingots_to_produce = int(input("Quantos lingotes de Bronze deseja produzir? "))
        inventory = get_inventory(dust_data)

        # 1. CÁLCULO INICIAL ("PLANO IDEAL")
        recipe = ALLOY_RECIPES["bronze"]
        total_ideal_mb = ingots_to_produce * INGOT_MB_VALUE
        
        # Cobre
        copper_target = total_ideal_mb * recipe["ideal_components"]["copper"]
        copper_inv = {k: v for k, v in inventory.items() if k in dust_data["copper"]}
        copper_sol, copper_mb, copper_inv_rem = solve_for_metal(copper_target, copper_inv, dust_data["copper"])

        # Estanho
        tin_target = total_ideal_mb * recipe["ideal_components"]["tin"]
        tin_inv = {k: v for k, v in inventory.items() if k in dust_data["tin"]}
        tin_sol, tin_mb, tin_inv_rem = solve_for_metal(tin_target, tin_inv, dust_data["tin"])

        # 2. VERIFICAÇÃO E AJUSTE
        final_total_mb = copper_mb + tin_mb
        if final_total_mb > 0:
            current_tin_ratio = tin_mb / final_total_mb
            min_tin, max_tin = recipe["rules"]["tin"]

            # Cenário 1: Estanho demais (seu caso)
            if current_tin_ratio > max_tin:
                print("\nAVISO: A proporção inicial de Estanho é muito alta ({:.1f}%).".format(current_tin_ratio * 100))
                print("Ajustando: Adicionando mais Cobre para balancear a liga...")
                # Calcula quanto cobre é necessário para o estanho atual estar no limite máximo
                needed_copper_mb = (tin_mb / max_tin) - tin_mb
                if needed_copper_mb > copper_mb:
                    additional_copper_needed = needed_copper_mb - copper_mb
                    # Resolve para o cobre adicional usando o inventário restante
                    copper_adjust_sol, copper_adjust_mb, _ = solve_for_metal(additional_copper_needed, copper_inv_rem, dust_data["copper"])
                    copper_sol = combine_solutions(copper_sol, copper_adjust_sol)
                    copper_mb += copper_adjust_mb

            # Cenário 2: Estanho de menos
            elif current_tin_ratio < min_tin:
                print("\nAVISO: A proporção inicial de Estanho é muito baixa ({:.1f}%).".format(current_tin_ratio * 100))
                print("Ajustando: Adicionando mais Estanho para balancear a liga...")
                needed_tin_mb = (copper_mb * min_tin) / (1 - min_tin)
                if needed_tin_mb > tin_mb:
                    additional_tin_needed = needed_tin_mb - tin_mb
                    tin_adjust_sol, tin_adjust_mb, _ = solve_for_metal(additional_tin_needed, tin_inv_rem, dust_data["tin"])
                    tin_sol = combine_solutions(tin_sol, tin_adjust_sol)
                    tin_mb += tin_adjust_mb

        # 3. EXIBIÇÃO DO RESULTADO FINAL
        print("\n" + "=" * 35)
        print("PLANO DE PRODUÇÃO OTIMIZADO E VÁLIDO")
        print(f"Para produzir ~{ingots_to_produce} lingotes de Bronze, use:")
        print("=" * 35)

        # Cobre
        print(f"\n--- Cobre (Total: {copper_mb:.0f} mB) ---")
        if not copper_sol: print("  Nenhum pó de Cobre necessário.")
        else:
            for dust, qty in copper_sol.items(): print(f"  - {qty}x {dust}")

        # Estanho
        print(f"\n--- Estanho (Total: {tin_mb:.0f} mB) ---")
        if not tin_sol: print("  Nenhum pó de Estanho necessário.")
        else:
            for dust, qty in tin_sol.items(): print(f"  - {qty}x {dust}")

        # Resumo final da liga
        final_total_mb = copper_mb + tin_mb
        final_copper_ratio = (copper_mb / final_total_mb * 100) if final_total_mb > 0 else 0
        final_tin_ratio = (tin_mb / final_total_mb * 100) if final_total_mb > 0 else 0
        
        print("\n--- Resumo da Liga ---")
        print(f"Total de mB na mistura: {final_total_mb:.0f}")
        print(f"Proporção Final: {final_copper_ratio:.1f}% Cobre / {final_tin_ratio:.1f}% Estanho")
        print(f"Lingotes produzidos: {math.floor(final_total_mb / INGOT_MB_VALUE)}")


    except (ValueError, ZeroDivisionError):
        print("Entrada inválida ou erro de cálculo. Tente novamente.")
    except KeyboardInterrupt:
        print("\nSaindo...")

if __name__ == "__main__":
    run_optimizer()
