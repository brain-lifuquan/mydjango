from django.db import models
from django.forms import ModelForm
from django.template import loader


class MyModel(models.Model):
    exclude_fields = []

    class Meta:
        abstract = True

    @classmethod
    def get_unique_fields(cls):
        # 主要应用场景是在删除对象时
        result = []
        # 首先判断 unique_together
        if cls._meta.unique_together:
            # unique_together 是集合的集合, 取集合的第一项
            return cls._meta.unique_together[0]
        # 然后是每个field是否是unique
        for field in cls._meta.get_fields():
            if field.name != 'id':
                if isinstance(field, models.ManyToOneRel):
                    continue
                if field.unique:
                    return [field.name]
                else:
                    result.append(field.name)
        # 执行到这里返回的是全部项
        return result

    @classmethod
    def get_upload_fields(cls):
        result = []
        for field in cls._meta.get_fields():
            # 排除exclude_fields 和 id
            if field.name not in cls.exclude_fields and field.name != 'id':
                # 排除 foreignkey
                if not isinstance(field, models.ManyToOneRel):
                    result.append({
                        'name': field.name,
                        'verbose_name': field.verbose_name,
                    })
        return result


class MyModelForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in iter(self.fields):
            # 给所有的field 添加class
            self.fields[field].widget.attrs.update({
                'class': 'form-control'
            })

    def as_form(self):
        # 使用自定义模板渲染form
        template = loader.get_template('form/form_template.html')
        form = template.render({'form': self})
        return form
