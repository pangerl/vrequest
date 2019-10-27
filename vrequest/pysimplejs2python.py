import re

def simplejs2python(s):
    s = '\n' + s
    s = re.sub(r'(\n *)function', r'\1def', s)
    for _ in range(10): s = re.sub(r'(\n *\}\n)', r'\n', s)
    s = re.sub(r'(\n *\}\n)', r'\n', s)
    s = re.sub(r'(\n *)\} *([^\n]+\n)', r'\1\2', s)
    s = re.sub(r' *\{ *\n', r':\n', s)
    s = re.sub(r'(\n *)(if *\([^\(\)]+\)) *([^\n\{:]+\n)', r'\1\2:\1    \3', s)   

    # 这里考虑处理简单的for循环条件的置换处理,不过这里有很大的变数要处理，后续再搞
    def deal_for(e):
        g = e.group(1)
        a,b,c = e.group(2),e.group(3),e.group(4)
        v = g + a.strip() + g + 'while ({}):'.format(b.strip()) + '  [{}]'.format(c.strip())
        return v
    s = re.sub(r'(\n *)for *\(([^;]*?);([^;]*?);([^;]*?)\):?', deal_for, s)
    def deal_while_1(s):
        q = []
        g = None
        k = None
        t = 0
        for i in s.splitlines():
            if t == 1:
                v = re.findall(r'^( *)', i)[0]
                if i.strip() != '':
                    if g is None:
                        g = len(v)
                    else:
                        if len(v) < g:
                            q.append(' '*g + k)
                            t = 2
            else:
                v = re.findall(r'^( *)(while[^\n]+)\[([^\n]+)\] *$', i)
                if v:
                    i = (v[0][0] + v[0][1]).rstrip()
                    k = v[0][2].strip()
                    t = 1
            q.append(i)
        q = '\n'.join(q)
        if re.findall(r'while[^\n]+\[([^\n]+)\]', q):
            return deal_while_1(q)
        else:
            return q
    s = deal_while_1(s)
    # 处理自增应该在处理循环之后
    s = re.sub(r'(\n *)([^\n]*?)([a-zA-Z0-9_$]+)( *\+\+)([^\n]*)', r'\1\2\3\5; \3 += 1', s)
    s = re.sub(r'(\n *)([^\n]*?)(\+\+ *)([a-zA-Z0-9_$]+)([^\n]*)', r'\1\4 += 1;\2\4\5', s)
    def deal_if_1(e):
        if e.group(2).strip().endswith(':'):
            return e.group(0)
        else:
            return e.group(1) + e.group(2) + ':'
    s = re.sub(r'(\n *)(if *\([^\n]*\))', deal_if_1, s)   
    s = re.sub(r'(\n *)else if', r'\1elif', s)
    s = re.sub(r'(\n *)else *', r'\1else:', s)
    s = re.sub(r'(\n *)var ', r'\1', s)
    s = re.sub(r'(\n *)//', r'\1#', s)
    def deal_comment_1(e):
        r = []
        for i in e.group(0).splitlines():
            i = i.strip('/ *')
            if i: r.append('# ' + i)
        return '\n'.join(r)
    s = re.sub(r'/\*.*?\*/', deal_comment_1, s, flags=re.S)
    s = re.sub(r'\n\n+', r'\n\n', s, flags=re.S)
    s = re.sub(r'\| *\n', r'| \\\n', s, flags=re.S)
    s = re.sub(r'; *;', r';', s)
    s = re.sub(r': *:', r':', s)
    s = re.sub(r'<<<', r'<<', s)
    s = re.sub(r'>>>', r'>>', s)
    s = re.sub(r'!==', r'!=', s)

    s = re.sub(r'((?:[a-zA-Z0-9_$]+(?:\[[a-zA-Z0-9_$]+\])* *\. *)*[a-zA-Z0-9_$]+(?:\[[a-zA-Z0-9_$]+\])*) *\. *length', r'len(\1)', s) # 处理 .length 函数为 len()
    def find_something(s, p='charAt', b='()'):
        o = re.findall(r'(?:[a-zA-Z0-9_$]+(?:\[[a-zA-Z0-9_$]+\])* *\. *)*[a-zA-Z0-9_$]+(?:\[[a-zA-Z0-9_$]+\])* *\. *' + p, s)
        if o:
            p = o[0]
            v = s.find(p)
            if v != -1:
                r = 0
                c = []
                for i in s[v+len(p):]:
                    t = False
                    if i == b[0]: r += 1; t = True
                    if i == b[1]: r -= 1; t = True
                    c.append(i)
                    if t and r == 0:
                        break
                v = ''.join(c)
                return o[0], v
    def replace_something(s, p='charAt', b='()'):
        cont = 0
        while True:
            cont += 1
            r = find_something(s, p, b)
            if r and cont <= 500:
                o, v = r
                if p == 'charAt': s = s.replace('.' + o.rsplit('.', 1)[-1] + v, '[{}]'.format(v.strip()[1:-1]))
                elif p == 'charCodeAt': s = s.replace(o + v, 'ord({}[{}])'.format(o.rsplit('.', 1)[0], v.strip()[1:-1]))
                elif p == 'fromCharCode': s = s.replace(o + v, 'bytes({}).decode()'.format(v))
            else:
                return s
    s = replace_something(s, p='charAt')
    s = replace_something(s, p='charCodeAt')
    s = replace_something(s, p='fromCharCode')

    # 这里考虑处理赋值的对齐,不过现在还是有点问题
    # s = re.sub(r'(\n *)([^\n=]+=[^\n=]+), *', r'\1\2', s)
    s = re.sub(r'_\$([a-zA-Z0-9_]{2})', r'_\1', s)    # 文书相关的处理
    s = re.sub(r'; *\n', r'\n', s)                    # 去除尾部分号(非必要)
    s = '''# 该功能仅用于简单的函数算法转换，
# 在一定程度上能方便更加青睐于纯 python 教徒对 js 翻译
# 请勿对翻译后的代码抱有过度信赖，该功能仅依赖于正则替换，所以生成代码很可能需要一定的微调。
''' + s
    return s.rstrip(' }\n')

if __name__ == '__main__':
    s = '''
// 123123
function _$TM() {
    var _$fz = [];
    for (var _$xA = 0; _$xA < 256; ++_$xA) {
        var _$F1 = _$xA;
        for (var _$vR = 0; _$vR < 8; ++_$vR) {
            if ((_$F1 & 0x80) !== 0)
                _$F1 = (_$F1 << 1) ^ 7;
            else
                _$F1 <<= 1;
        }
        _$fz[_$xA] = _$F1 & 0xff;
    }
    return _$fz;
'''
    print(simplejs2python(s))