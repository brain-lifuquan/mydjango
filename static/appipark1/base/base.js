//格式化字符串
String.prototype.format = function () {
    let values = arguments;
    return this.replace(/{(\d+)}/g, function (match, index) {
        if (values.length > index) {
            return values[index];
        } else {
            return "";
        }
    });
};　　

//解决ajax的csrf
jQuery(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            let cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                let cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        let host = document.location.host; // host + port
        let protocol = document.location.protocol;
        let sr_origin = '//' + host;
        let origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url === origin || url.slice(0, origin.length + 1) === origin + '/') ||
            (url === sr_origin || url.slice(0, sr_origin.length + 1) === sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});
//新增和编辑按钮逻辑
function modify_obj(title, content, get_data) {
    console.log('enter modify_obj');
    //需要构造一个js对象obj传给add_obj函数，obj对象包括title--弹窗标题 content-- 弹窗html get_formdata()--获取传送函数 3个属性
    layer.open({type:1,shade:0.5,btn:['提交','返回'],//area: ['500px','500px'],
        title: title, content: content,
        yes:function () {
            $.ajax({
                //contentType: false, processData: false, 不处理post的数据
                //post到服务器的数据采用FormData()格式
                url: '', type: 'post', contentType: false, processData: false,
                data: get_data(),
                success: function (data) {
                    if (data === 'OK'){location.href='';} else {$('#errmsg').text(data);}
                }
            });
        }
    });
}
//通过id从服务器获取数据
function get_obj(obj_id) {
    console.log('enter get_obj');
    //从服务器获取指定id的信息
    let result = '';
    //此处需要同步执行，async false  dataType 指定服务器返回的数据类型
    $.ajax({url: '', type: 'post', async: false, dataType: 'json',
        data: {'post_type': 'get','id': obj_id},
        success: function (data) {result = data;}
    });
    //console.log(result);
    return result;
}
//show_page
function show_page(current_page, per_page) {
    console.log('enter show_page', current_page, per_page);
    let post_data = {
        'post_type': 'show_page',
        'current_page': current_page,
        'per_page': per_page
    };
    $.ajax({
        url: '', type: 'post', data: post_data,
        success: function (data) {if (data === 'OK') {location.href = "";} else {layer.msg(data);}}
    });
}
//注册事件
$(document).ready(function () {
    //点击删除按钮
    $('button.delete-obj').click(function () {
        console.log("you clicked delete-obj button !");
        //此时的this指的是button -父节点td-父节点tr-子节点label-子节点input
        let obj_id = $(this).parent('td').parent('tr').children('td').children('label').children('input.checkbox').val();
        let obj = get_obj(obj_id);
        let title = "删除提示";
        let name = obj.name;
        if (name === undefined ){
            name = '';
        }
        let delete_content = '<div class="pl-3 pr-3">\
            <p>确认要删除 {0} {1} 吗？</p>\
            <p><span class="errmsg" id="errmsg"></p>\
            </div>'.format(obj.class, name);
        let get_delete_data = function () {
            let data = new FormData();
            data.append('post_type', 'delete');
            data.append('id', obj_id);
            return data;
        };
        modify_obj(title, delete_content, get_delete_data);
    });
    //点击恢复按钮
    $('button.recover-obj').click(function () {
        console.log("you clicked delete-obj button !");
        //此时的this指的是button -父节点td-父节点tr-子节点label-子节点input
        let obj_id = $(this).parent('td').parent('tr').children('td').children('label').children('input.checkbox').val();
        let obj = get_obj(obj_id);
        let title = "恢复提示";
        let name = obj.name;
        if (name === undefined ){
            name = '';
        }
        let recover_content = '<div class="pl-3 pr-3">\
            <p>确认要恢复 {0} {1} 吗？</p>\
            <p><span class="errmsg" id="errmsg"></p>\
            </div>'.format(obj.class, name);
        let get_recover_data = function () {
            let data = new FormData();
            data.append('post_type', 'recover');
            data.append('id', obj_id);
            return data;
        };
        modify_obj(title, recover_content, get_recover_data);
    });
    //点击全选input
    $('input#select_all').click(function () {
        console.log('you clicked select_all');
        let box = document.getElementById('select_all');
        let checks = document.getElementsByName('table_checkbox');
        if (box.checked) {
            for (let i=0; i<checks.length; i++) {
                checks[i].checked = true;
            }
        } else {
            for (let i=0; i<checks.length; i++) {
                checks[i].checked = false;
            }
        }
    });
    //点击批量删除按钮
    $('button#delete-some').click(function () {
        console.log("you clicked delete-some button !");
        let list = [];
        $("input:checked").each(function () {
            list.push($(this).val());
        });
        if (list.length === 0) {
            layer.msg('至少要选中一行数据！');
        } else {
            //判断是否包含全选, 如果包含，把全选去掉
            let index = list.indexOf('all');
            if(index > -1){
                list.splice(index,1);
            }
            let str = list.join(',');
            let title = "批量删除提示";
            let delete_some_content = '<div class="pl-3 pr-3">\
                <p >确定要删除选中的 {0} 个对象吗？</p>\
                <p><span class="errmsg" id="errmsg"></p>\
                </div>'.format(list.length);
            let get_delete_some_data = function () {
                let data = new FormData();
                data.append('post_type', 'delete_some');
                data.append('ids', str);
                return data;
            };
            modify_obj(title, delete_some_content, get_delete_some_data);
        }
    });
    //set-per_page
    $('a.set-per_page').click(function () {
        console.log("you clicked set_per_page button!");
        let per_page = $(this).attr('value');
        console.log("per_page is", per_page);
        show_page(1,per_page);
    });
    //set-current_page
    $('a.set-current_page').click(function () {
        console.log("you clicked set_current_page button!");
        let current_page = $(this).attr('value');
        let per_page = $('ul.pagination').attr('per_page');
        console.log("current_page is", current_page);
        console.log("per_page is", per_page);
        show_page(current_page,per_page);
    });
    //点击查询按钮
    $('button.query_button').click(function () {
        console.log("you clicked query_button!");
        let post_data = {'post_type': 'query', 'query_str': get_query_str()};
        $.ajax({
            url: '', type: 'post', data: post_data,
            success: function (data) {if (data === 'OK') {location.href = "";} else {layer.msg(data);}}
        });
    });
    // 改变显示删除状态
    $('button.change-deleted_visible').click(function () {
        console.log("you clicked change-deleted_visible button!");
        let deleted_visible = $(this).attr('value');
        $.ajax({
            url: '', type: 'post', data: {'post_type': 'change_deleted_visible', 'deleted_visible': deleted_visible},
            success: function (data) {
                if (data === 'OK') { location.href = '';} else { layer.msg(data);}
            }
        });
    });
});