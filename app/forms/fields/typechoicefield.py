from django.forms.fields import ChoiceField


class TypeChoiceField(ChoiceField):

    def __init__(self, *, types=None, **kwargs):
        # types 应该是一个字典 包含 2个key display 和 inner
        # key display 对应显示值列表
        # key inner 对应内部值列表
        # 两个列表顺序对应，最后1个值是default值
        choices = ()
        if types:
            choices = [(inner, display) for inner, display in zip(types['inner'][:-1], types['display'][:-1])]
        super().__init__(choices=choices, **kwargs)
        self.types = types

    def to_python(self, value):
        if value in self.types['inner']:
            return value
        elif value in self.types['display']:
            _index = self.types['display'].index(value)
            return self.types['inner'][_index]
        else:
            return self.types['inner'][-1]
