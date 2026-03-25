# Filtros de ORDER BY Visual.

def parse_sort(sort_string):
    sort_items = []
    sort_map = {}

    if not sort_string:
        return sort_items, sort_map

    for item in sort_string.split(','):
        item = item.strip()
        if not item or ':' not in item:
            continue

        campo, direcao = item.split(':', 1)
        campo = campo.strip()
        direcao = direcao.strip().lower()

        if campo not in ['ativo', 'categoria','data', 'estoque', 'nome', 'nome_cliente', 'pagamentos','preco', 'p_custo', "lucro", 'total', 'status']:
            continue

        if direcao not in ['asc', 'desc']:
            direcao = 'asc'

        if campo not in sort_map:
            sort_items.append((campo, direcao))
            sort_map[campo] = direcao

    return sort_items, sort_map

def toggle_sort(sort_string, campo):
    sort_items, sort_map = parse_sort(sort_string)

    novos = []
    campo_encontrado = False

    for campo_atual, direcao_atual in sort_items:
        if campo_atual == campo:
            campo_encontrado = True
            nova_direcao = 'desc' if direcao_atual == 'asc' else 'asc'
            novos.append((campo_atual, nova_direcao))
        else:
            novos.append((campo_atual, direcao_atual))

    if not campo_encontrado:
        novos.append((campo, 'asc'))

    return ','.join(f'{campo}:{direcao}' for campo, direcao in novos)

