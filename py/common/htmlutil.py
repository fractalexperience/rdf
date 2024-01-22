
def wrap_table(o, attr=None):
    """ attrs => Any additional attributes """
    if attr is None:
        attr = 'class="table table-hover table-bordered"'
    o.insert(0, f'<table {attr}>')
    o.append('</table>')


def wrap_h(o, fields, title, attr=None):
    s = ''.join([f'<th>{f}</th>' for f in fields])
    o.insert(0, f'<tr>{s}</tr>')
    if title:
        o.insert(0, f'<h2>{title}</h2>')
    wrap_table(o, attr)


def wrap_td(o, cell):
    if isinstance(cell, str) or isinstance(cell, int) or isinstance(cell, float):
        o.append(f'<td>{cell}</td>')
        return
    if isinstance(cell, tuple):
        o.append(f'<td {cell[0]}>{cell[1]}</td>')


def wrap_tr(o, cells, attr=None):
    o2 = []
    for c in cells:
        wrap_td(o2, c)
    if attr is None:
        o2.insert(0, '<tr>')
    else:
        o2.insert(0, f'<tr {attr}>')
    o2.append('</tr>')
    o.append(''.join(o2))

