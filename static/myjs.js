// 显示带标题和按钮的模态对话框
function show_dialog(option) {
    if ($('#mymodal') !== undefined) {
        $('#mymodal').remove();
    }
    let mymodal = '<div class="modal" id="mymodal" tabindex="-1" role="dialog">\n' +
        '  <div class="modal-dialog modal-dialog-centered">\n' +
        '    <div class="modal-content">\n' +
        '      <div class="modal-header">\n' +
        '        <h5 class="modal-title">{0}</h5>\n' +
        '        <button type="button" class="close" data-dismiss="modal" aria-label="Close">\n' +
        '          <span aria-hidden="true">&times;</span>\n' +
        '        </button>\n' +
        '      </div>\n' +
        '      <div class="modal-body">\n' +
        '        {1}\n' +
        '      </div>\n' +
        '      <div class="modal-footer">\n' +
        '        <button type="button" class="btn btn-primary" id="mymodal_confirmButton">确定</button>\n' +
        '        <button type="button" class="btn btn-secondary" data-dismiss="modal">取消</button>\n' +
        '      </div>\n' +
        '    </div>\n' +
        '  </div>\n' +
        '</div>';
    $('body').append(mymodal.format(option.title, option.content));
    // 给modal添加hidden事件
    $('#mymodal').on('hidden.bs.modal', function () {
        $(this).remove();
        // $('.modal-backdrop').remove();
    });
    // 给确定按钮添加 click事件
    $('#mymodal_confirmButton').on('click', function () {
        // 执行callback
        option.confirm();
        // 关闭对话框  hide以后会自动删除modal 因此 hide要在执行callback之后，不然callback无法使用modal之中的内容
        $('#mymodal').modal('hide');
    });
    $('#mymodal').modal('show');
}

// 显示不带标题和按钮的模态对话框
function show_msg(msg) {
    if ($('#mymodal') !== undefined) {
        $('#mymodal').remove();
    }
    // modal 格式
    let mymodal = '<div class="modal" id="mymodal" tabindex="-1" role="dialog">\n' +
        '    <div class="modal-dialog modal-dialog-centered">\n' +
        '        <div class="modal-content">\n' +
        '            <div class="modal-body">\n' +
        '                <button type="button" class="close" data-dismiss="modal" aria-label="Close">\n' +
        '                    <span aria-hidden="true">&times;</span>\n' +
        '                </button>\n' +
        '                <div id="msgModal-body">\n' +
        '                    {0}\n' +
        '                </div>\n' +
        '            </div>\n' +
        '        </div>\n' +
        '    </div>\n' +
        '</div>';
    $('body').append(mymodal.format(msg));
    // 给modal添加hidden事件
    $('#mymodal').on('hidden.bs.modal', function () {
        $(this).remove();
        // $('.modal-backdrop').remove();
    });
    $('#mymodal').modal('show');
}

function show_errmsg(respon) {
    show_msg(respon.errmsg.join('<br>'));
}

// 显示旋转的加载图标
function show_spinner() {
    if ($('#mymodal') !== undefined) {
        $('#mymodal').remove();
    }
    // modal 格式
    let mymodal = '<div class="modal" id="mymodal" data-backdrop="static" data-keyboard="false" tabindex="-1" role="dialog">\n' +
        '    <div class="modal-dialog modal-dialog-centered" style="width: 100px">\n' +
        '        <div class="modal-content">\n' +
        '            <div class="modal-body">\n' +
        '                <div id="msgModal-body">\n' +
        '                    <div class="d-flex justify-content-center">\n' +
        '                        <div class="spinner-border" role="status">\n' +
        '                            <span class="sr-only">Loading...</span>\n' +
        '                        </div>\n' +
        '                    </div>' +
        '                </div>\n' +
        '            </div>\n' +
        '        </div>\n' +
        '    </div>\n' +
        '</div>';
    $('body').append(mymodal);
    // 给modal添加hidden事件
    $('#mymodal').on('hidden.bs.modal', function () {
        $(this).remove();
        // 某些情况下 backdrop 删不掉
        $('.modal-backdrop').remove();
    });
    $('#mymodal').modal('show');
}


// 在发送ajax时添加csrf_token
$(document).ajaxSend(function (event, xhr, settings) {
    // 检查ajax的method event是事件  xhr是请求  settings是ajax的配置信息
    function safeMethod(method) {
        // 使用正则表达式检查 mothod get 等几个方法是安全方法 不需要带csrf_token
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    // 检查url是否同源。。。  域名或ip。。 host
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        let host = document.location.host; // host + port
        let protocol = document.location.protocol;  //协议
        let sr_origin = '//' + host;
        let origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        if (!(/^(\/\/|http:|https:).*/.test(url))) {
            // 使用相对路径说明是同源 url不以// 或 http:/https: 开头
            return true;
        } else if (url === sr_origin || url.slice(0, sr_origin.length + 1) === sr_origin + '/') {
            // url以 // 开头的情况，不携带协议信息
            return true;
        } else {
            // url 携带协议信息的情况
            return url === origin || url.slice(0, origin.length + 1) === origin + '/';
        }
    }

    // 查询cookie
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            let cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                // $.trim(str)移除字符串开始和末尾处的所有换行符，空格(包括连续的空格)和制表符。如果这些空白字符在字符串中间时，它们将被保留，不会被移除。
                let cookie = $.trim(cookies[i]);
                // 截取cookie =号前的部分 与name进行对比
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    // 比对通过，获得需要的cookie
                    // decodeURIComponent(URIstring) 对 encodeURIComponent() 函数编码的 URI 进行解码。将十六进制转义序列替换为它们表示的字符
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // settings.type 对应 发送ajax 时的type信息 settings.url 是ajax的 url配置
    // console.log('enter ajaxSend');
    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        // 将X-CSRFToken 加入道 request的头信息中
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

// 字符串format
String.prototype.format = function () {
    // Javascrip中每个函数都会有一个Arguments对象实例arguments，它引用着函数的实参，可以用数组下标的方式"[]"引用arguments的元素。
    // 如果没有参数，直接返回原字符串
    if (arguments.length === 0) {
        return this;
    }
    // 遍历参数
    let s = this;
    for (let i = 0; i < arguments.length; i++) {
        // 按顺序使用参数替换占位符
        // RegExp 对象表示正则表达式  g 执行全局匹配
        s = s.replace(new RegExp('\\{' + i + '\\}', 'g'), arguments[i]);
    }
    return s;
};

// 对Date的扩展，将 Date 转化为指定格式的String
// (new Date()).Format("yyyy-MM-dd hh:mm:ss.S") ==> 2006-07-02 08:09:04.423
Date.prototype.format = function (fmt) {
    let o = {
        "M+": this.getMonth() + 1,                 //月份
        "d+": this.getDate(),                    //日
        "h+": this.getHours(),                   //小时
        "m+": this.getMinutes(),                 //分
        "s+": this.getSeconds(),                 //秒
        "q+": Math.floor((this.getMonth() + 3) / 3), //季度
        "S": this.getMilliseconds()             //毫秒
    };
    if (/(y+)/.test(fmt))
        fmt = fmt.replace(RegExp.$1, (this.getFullYear() + "").substr(4 - RegExp.$1.length));
    for (const k in o)
        if (new RegExp("(" + k + ")").test(fmt))
            fmt = fmt.replace(RegExp.$1, (RegExp.$1.length === 1) ? (o[k]) : (("00" + o[k]).substr(("" + o[k]).length)));
    return fmt;
};

// 封装$.ajax
function myajax(option) {
    $.ajax({
        url: option.url,
        type: 'post',
        dataType: 'json',
        contentType: false,
        processData: false,
        data: option.data,
        success: function (respon) {
            $('#mymodal').modal('hide');
            if (respon.code > 0) {
                show_errmsg(respon);
            } else {
                option.success(respon);
            }
        },
        beforeSend: function (XMLHttpRequest) {
            show_spinner();
        },
        error: function (XMLHttpRequest, textStatus, errorThrown) {
            $('#mymodal').modal('hide');
            if (XMLHttpRequest.status === 500) {
                let msg = XMLHttpRequest.responseText.split('\n');
                // 找到msg中的第一个空行
                let i;
                for (i = 0; i < msg.length; i++) {
                    if (msg[i] === "") break;
                }
                msg = msg.slice(0, i);
                show_msg(msg.join('<br>'));
            } else {
                show_msg(
                    '错误信息：<br> XMLHttpRequest.status--{0} <br> errorThrown--{1} '
                        .format(XMLHttpRequest.status, errorThrown));
            }
        },
    });
}

// 将data中的数据 按照fields要求 输出到csv_name 命名的 csv文件 并下载
function to_csv(data, csv_name, fields) {
    // csv_str 是最终写入csv的字符串
    let csv_str = "";
    // cols 存储列头
    let cols = [];
    if (fields) {
        // 如果传递了 fields参数, 则从 fields中获取表头信息
        for (const field of fields) {
            cols.push(field.name);
            csv_str += '"{0}",'.format(field.verbose_name);
        }
    } else {
        // 如果没有fields 则从第一行数据提取表头信息
        for (const col in data[0]) {
            cols.push(col);
            csv_str += '"{0}",'.format(col);
        }
    }
    csv_str += '\n';
    for (const row of data) {
        for (const col of cols) {
            let str = row[col];
            if (str) {
                // 如果文本中存在 双引号或逗号, 需要将 双引号替换成 "" 两个双引号
                if (str.match(/[\s,"]/)) {
                    str = str.replace(/"/g, '""');
                    csv_str += '"{0}",'.format(str);
                } else {
                    csv_str += '"{0}",'.format(str);
                }
            }
        }
        csv_str += '\n';
    }
    let uri = 'data:text/csv;charset=utf-8,\ufeff' + encodeURIComponent(csv_str);
    let link = document.createElement('a');
    link.href = uri;
    link.download = csv_name;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// bootstrap-table row-toolbar
function operate_formatter(value, row, index) {
    return $('#row_toolbar').html();
}

// 使用bootstrap-table渲染表格
function show_bootstrap_table() {
    // 渲染表格
    $('#table').bootstrapTable({
        // 获取数据
        url: '#',
        method: 'post',
        contentType: 'application/x-www-form-urlencoded',
        dataType: 'json',
        queryParams: function (params) {
            return {
                post_type: 'query',
            }
        },
        responseHandler: function (reson) {
            // 因为在渲染table时修改了toolbar的html代码，需要刷新tooltip
            $('[data-toggle="tooltip"]').tooltip();
            if (reson.code !== 0) {
                show_msg(reson.errmsg.join(''));
            } else {
                return reson.data;
            }
        },
        // bootstrap-table 搜索开关
        search: true,
        // bootstrap-table 搜索相关参数
        visibleSearch: true,
        strictSearch: false,
        showSearchButton: true,
        searchOnEnterKey: true,
        // bootstrap-table 头部工具栏设置
        toolbar: '#toolbar',
        showRefresh: true,
        showColumns: true,
        // 分页参数
        pagination: true,
        sidePagination: 'client',
        pageSize: 10,
        pageList: '[10, 20, 50, All]',
        paginationHAlign: 'left',
        paginationDetailHAlign: 'right',
        paginationVAlign: 'bottom',
        paginationPreText: '上一页',
        paginationNextText: '下一页',
        // 定义图标大小 样式
        iconSize: 'sm',
        buttonsClass: 'primary',
    });
}
