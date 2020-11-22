jQuery(document).ajaxSend(function(event, xhr, settings) {
    //解决ajax的csrf
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

String.prototype.format = function () {
    // Javascrip中每个函数都会有一个Arguments对象实例arguments，它引用着函数的实参，可以用数组下标的方式"[]"引用arguments的元素。
    // 如果没有参数，直接返回原字符串
    if(arguments.length === 0){
        return this;
    }
    // 遍历参数
    let s = this;
    for(let i=0; i<arguments.length; i++){
        // 按顺序使用参数替换占位符
        // RegExp 对象表示正则表达式  g 执行全局匹配
        s = s.replace(new RegExp('\\{' + i + '\\}', 'g'), arguments[i]);
    }
    return s;
};

function get_form_content(form_name, form_str) {
    // 将form_str包装成jquery对象 然后找到其中的li 并添加class
    let lis = $('<div>{0}</div>'.format(form_str)).find('li').addClass("list-group-item");
    let arr_lis = [];
    for(let i=0; i<lis.length; i++){
        arr_lis.push(lis[i].outerHTML);
    }
    // 加入外层包装
    return '<form name="{0}"><ul class="list-group">{1}</ul></form>'.format(form_name, arr_lis.join(''));
}

function show_modal_right(title, content, callback) {
    return layer.open({
        type: 1,  //弹窗类型 1表示模态对话框
        closeBtn: 0,  //右上角的关闭按钮
        offset: 'r',  // 表示弹窗位置
        area: ['40%', '100%'],  // 表示弹窗大小 顺序 宽度 高度 可用绝对值或相对值
        shade: 0.5,   //遮罩层透明度
        btn:['提交','返回'],  // 底部按钮
        title: title,
        content: content,
        yes: callback
    });
}

function show_modal(title, content, callback) {
    return layer.open({
        type: 1,
        closeBtn: 0,
        shade: 0.5,
        btn: ['提交', '返回'],
        title: title,
        content: content,
        yes: callback
    });
}

function get_formdata(post_type) {
    let post_data = new FormData();
    let form = $('form[name="{0}"]'.format(post_type))[0];
    if (form !== undefined) {
        post_data = new FormData(form);
    }
    post_data.append('post_type', post_type);
    return post_data;
}

function myajax(url, post_data, callback) {
    $.ajax({
        url: url,
        type: 'post',
        contentType: false,
        processData: false,
        dataType: 'json',
        data: post_data,
        success: function (respon) {
            if (respon.msg !== 'success') {
                show_errmsg(respon.errmsg);
            } else {
                callback(respon);
            }
        }
    });
}

function show_errmsg(errmsg) {
    layer.msg(
        errmsg.join('\n'),
        {time: 6000}
        );
}
