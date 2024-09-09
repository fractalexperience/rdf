
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


def wrap_td(o, cell, is_th=False):
    if cell is None:
        o.append('<td>&nbsp;</td>')
        return
    tag = "th" if is_th else 'td'
    if cell == 'NULL':  # Special case for null values
        o.append(f'<{tag} class="table-secondary">{cell}</{tag}>')
        return
    if isinstance(cell, str) or isinstance(cell, int) or isinstance(cell, float):
        o.append(f'<{tag}>{cell}</{tag}>')
        return
    if isinstance(cell, tuple):
        o.append(f'<{tag} {cell[0]}>{cell[1]}</{tag}>')


def wrap_tr(o, cells, attr=None, is_th=False):
    o2 = []
    for c in cells:
        wrap_td(o2, c, is_th=is_th)
    if attr is None:
        o2.insert(0, '<tr>')
    else:
        o2.insert(0, f'<tr {attr}>')
    o2.append('</tr>')
    o.append(''.join(o2))


def append_interactive_table(o):
    o.append("""
    <script>
    $('.dataTable').each(function () {
        var t = $(this).DataTable({
            "paging":true,
            "ordering":true,
            "info":true,
            "pageLength": 50})
        t.order([]).draw();
    });
    </script> """)
