from lark import Lark, Transformer

grammar = '!n_main: n_ip\n!n_ip: n_number xrule_0 n_number xrule_0 n_number xrule_0 n_number\n!n_number: n_from_0_to_255\n!n_from_0_to_255: /[0-9]/\n    |/[1-9]/ /[0-9]/\n    |xrule_1 /[0-9]/ /[0-9]/\n    |xrule_2 /[0-4]/ /[0-9]/\n    |xrule_2 xrule_3 /[0-5]/\n!xrule_0: "."\n!xrule_1: "1"\n!xrule_2: "2"\n!xrule_3: "5"'

from js2py.pyjs import *
# setting scope
var = Scope( JS_BUILTINS )
set_global_object(var)

# Code follows:
var.registers(['id'])
@Js
def PyJsHoisted_id_(x, this, arguments, var=var):
    var = Scope({'x':x, 'this':this, 'arguments':arguments}, var)
    var.registers(['x'])
    return var.get('x').get('0')
PyJsHoisted_id_.func_name = 'id'
var.put('id', PyJsHoisted_id_)
pass
pass

class TransformNearley(Transformer):
    __default__ = lambda self, n, c, m: c if c else None

parser = Lark(grammar, start="n_main", maybe_placeholders=False)
def parse(text):
    return TransformNearley().transform(parser.parse(text))

