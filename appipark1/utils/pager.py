# -*- coding: utf-8 -*-


class Pager(object):
    def __init__(self, current_page, total_items, per_page=20, show_pages=5):
        self.current_page = int(current_page)
        self.per_page = int(per_page)
        self.total_items = int(total_items)
        self.show_pages = int(show_pages)
        # divmod 返回（商，余数）元组
        result = divmod(self.total_items, self.per_page)
        if result[1]:
            # 如果余数不为0，总页数需要加1
            self.total_pages = result[0] + 1
        else:
            self.total_pages = result[0]

    def start(self):
        return (self.current_page-1)*self.per_page

    def end(self):
        return self.current_page*self.per_page

    def pager(self):
        half = divmod(self.show_pages, 2)[0]
        if self.total_pages <= self.show_pages:
            # 总页数较少时，显示全部页码
            begin = 1
            end = self.total_pages
        else:
            # 总页数交多，显示指定数量的页码
            if self.current_page <= half:
                # 当前页较小，显示前几页
                begin = 1
                end = self.show_pages
            elif self.current_page > (self.total_pages - half):
                # 当前页较大，显示最后几页
                begin = self.total_pages - self.show_pages + 1
                end = self.total_pages
            else:
                # 正常显示
                begin = self.current_page - half
                end = self.current_page + half
        page_list = []
        # 首页
        temp = '''
        <li class="page-item">
            <a class="page-link set-current_page" value=1 href="#" >首页</a>
        </li>
        '''
        page_list.append(temp)
        # 页码
        for i in range(begin, end+1):
            if i == self.current_page:
                temp = '''
                <li class="page-item">
                    <a class="page-link active" >%d</a>
                </li>
                ''' % i
            else:
                temp = '''
                <li class="page-item">
                    <a class="page-link set-current_page" value=%d href="#">%d</a>
                </li>
                ''' % (i, i)
            page_list.append(temp)
        # 末页
        temp = '''
        <li class="page-item">
            <a class="page-link set-current_page" value=%d href="#">末页</a>
        </li>
        ''' % self.total_pages
        page_list.append(temp)
        # 设置per_page
        temp = '''
        <li>
            <div class="btn-group dropup">
                <button type="button" class="btn btn-info dropdown-toggle" data-toggle="dropdown"
                    aria-haspopup="true" aria-expanded="false">
                    %d条/每页
                </button>
                <div class="dropdown-menu">
                    <a class="dropdown-item set-per_page" value=10>10条/每页</a>
                    <a class="dropdown-item set-per_page" value=20>20条/每页</a>
                    <a class="dropdown-item set-per_page" value=50>50条/每页</a>
                    <a class="dropdown-item set-per_page" value=100>100条/每页</a>
                </div>
            </div>
        </li>
        ''' % self.per_page
        page_list.append(temp)
        return ''.join(page_list)
