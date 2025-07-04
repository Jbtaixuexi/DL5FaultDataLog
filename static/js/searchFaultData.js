document.addEventListener('DOMContentLoaded', function () {
    const faultTableBody = document.getElementById('faultTableBody');
    const searchForm = document.getElementById('searchForm');
    const paginationElement = document.getElementById('pagination');
    const DEFAULT_PAGE_SIZE = 20;
    let currentPage = 1;
    let totalPages = 1;

    function sendSearchRequest(page = 1) {
        console.log('Debug - sendSearchRequest called', page);
        // 更新当前页
        currentPage = page;

        // 获取表单数据并转换为对象
        const formData = new FormData(searchForm);
        const pageSizeElement = document.getElementById('pageSizeSelect');
        const pageSizeValue = pageSizeElement ? pageSizeElement.value : DEFAULT_PAGE_SIZE;
        const data = {
            page: currentPage,
            page_size: pageSizeValue,
        };
        [
            'trainNumber', 'status', 'dateRange', 'parts',
            'expiringDays', 'expiredDays'
        ].forEach(field => {
            data[field] = formData.get(field);
        });
        // 清理空字符串参数
        const cleanedData = Object.fromEntries(
            Object.entries(data).filter(([_, v]) => v !== '' && v !== null && v !== undefined)
        );

        // 发送POST请求
        fetch('/faults/search_fault_data/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify(cleanedData)
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(result => {
                if (result.error) {
                    console.error('Server error:', result.error);
                    return;
                }

                // 更新总页数
                totalPages = result.total_pages;

                // 渲染表格数据
                renderTable(result.records);

                // 渲染分页控件
                renderPagination(result.page, result.total_pages);
            })
            .catch(error => {
                console.error('请求出错:', error);
            });
    }

    function renderTable(records) {
        console.log('Received records:', records);
        faultTableBody.innerHTML = '';

        if (records.length === 0) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 10; // 根据你的列数调整
            cell.textContent = '没有找到匹配的记录';
            cell.classList.add('text-center', 'py-4');
            row.appendChild(cell);
            faultTableBody.appendChild(row);
            return;
        }

        // 注意：这里使用后端返回的字段名，与views.py中一致
        records.forEach(item => {
            const row = document.createElement('tr');

            // 复选框列
            const checkboxCell = document.createElement('td');
            checkboxCell.innerHTML = '<input type="checkbox">';
            row.appendChild(checkboxCell);

            // 使用模板字符串创建所有列
            row.innerHTML += `
            <td>${item.date || ''}</td>
            <td>${item.time || ''}</td>
            <td>${item.train_number || ''}</td>
            <td>${item.source || ''}</td>
            <td>${item.fault_type || ''}</td>
            <td title="${item.phenomenon || ''}">${item.phenomenon ? item.phenomenon.substring(0, 20) + (item.phenomenon.length > 20 ? '...' : '') : ''}</td>
            <td>${item.location || ''}</td>
            <td>${item.status || ''}</td>
            <td>${item.technician || ''}</td>
            <td>${item.system || ''}</td>
            <td>${item.secondary || ''}</td>
            <td>${item.third || ''}</td>
            <td>${item.fourth || ''}</td>
            <td title="${item.cause || ''}">${item.cause ? item.cause.substring(0, 20) + (item.cause.length > 20 ? '...' : '') : ''}</td>
            <td>${item.reporter || ''}</td>
            <td>${item.receiver || ''}</td>
            <td title="${item.progress || ''}">${item.progress ? item.progress.substring(0, 20) + (item.progress.length > 20 ? '...' : '') : ''}</td>
            <td>${item.expected_date || ''}</td>
            <td title="${item.solution || ''}">${item.solution ? item.solution.substring(0, 20) + (item.solution.length > 20 ? '...' : '') : ''}</td>
            <td>${item.part_replaced ? '是' : '否'}</td>
            <td>${item.part_name || ''}</td>
            <td>${item.part_quantity || ''}</td>
            <td>${item.materials || ''}</td>
            <td>${item.tools || ''}</td>
            <td>${item.location_time || ''}</td>
            <td>${item.replacement_time || ''}</td>
            <td>${item.legacy_date || ''}</td>
            <td>${item.registrar || ''}</td>
            <td>${item.registration_time || ''}</td>
            <td>${item.is_valid ? '是' : '否'}</td>
            <td>${item.image_count || ''}</td>
            <td title="${item.image_paths || ''}">${item.image_paths ? '查看' : ''}</td>
            <td>${item.modified_by || ''}</td>
            <td>${item.modified_at || ''}</td>
        `;
            faultTableBody.appendChild(row);
        });
    }

    function renderPagination(currentPage, totalPages) {
        paginationElement.innerHTML = '';

        if (totalPages <= 1) return;

        // 添加上一页按钮
        const prevLi = document.createElement('li');
        prevLi.className = 'page-item' + (currentPage === 1 ? ' disabled' : '');
        prevLi.innerHTML = `
            <a class="page-link" href="#" aria-label="Previous" data-page="${currentPage - 1}">
                <span aria-hidden="true">&laquo;</span>
            </a>
        `;
        paginationElement.appendChild(prevLi);

        // 添加页码按钮
        const startPage = Math.max(1, currentPage - 2);
        const endPage = Math.min(totalPages, currentPage + 2);

        for (let i = startPage; i <= endPage; i++) {
            const pageLi = document.createElement('li');
            pageLi.className = 'page-item' + (i === currentPage ? ' active' : '');
            pageLi.innerHTML = `<a class="page-link" href="#" data-page="${i}">${i}</a>`;
            paginationElement.appendChild(pageLi);
        }

        // 添加下一页按钮
        const nextLi = document.createElement('li');
        nextLi.className = 'page-item' + (currentPage === totalPages ? ' disabled' : '');
        nextLi.innerHTML = `
            <a class="page-link" href="#" aria-label="Next" data-page="${currentPage + 1}">
                <span aria-hidden="true">&raquo;</span>
            </a>
        `;
        paginationElement.appendChild(nextLi);

        // 添加分页事件监听
        paginationElement.querySelectorAll('.page-link').forEach(link => {
            link.addEventListener('click', function (e) {
                e.preventDefault();
                const page = parseInt(this.getAttribute('data-page'));
                if (!isNaN(page)) {
                    sendSearchRequest(page);
                }
            });
        });
    }

    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    // 页面加载完成后发送空搜索请求
    sendSearchRequest();

    // 搜索按钮事件
    document.getElementById('searchBtn').addEventListener('click', function (event) {
        event.preventDefault();
        sendSearchRequest(1); // 重置到第一页
    });
});

document.addEventListener('DOMContentLoaded', function () {
    // 初始化日期字段
    initDateFields();

    // 初始化车号选择器
    initTrainNumberSelect();

    // 加载第一页数据
    searchFaults(1);

    // 初始化备件更换显示控制
    initPartReplacementToggle();

    // 初始化搜索功能
    initSearchFunctionality();

    // 初始化导出功能
    initExportFunctionality();

    // 初始化删除功能
    initDeleteFunctionality();

    // 初始化编辑功能
    initEditFunctionality();

    // 初始化新增故障表单
    initAddFaultForm();

    // 初始化日期范围选择器
    initDateRangePicker();

    // 初始化状态选择器
    initStatusSelectors();

    // 初始化故障分类联动选择
    initFaultClassification();
});

// 在DOMContentLoaded事件内添加以下代码
document.addEventListener('DOMContentLoaded', function () {
    // 初始化日期选择器
    flatpickr("#searchDateRange", {
        mode: "range",
        locale: "zh",
        dateFormat: "Y-m-d",
        allowInput: true,
        static: true,
        onChange: function (selectedDates, dateStr) {
            if (selectedDates.length === 2) {
                // 设置隐藏输入框的值
                document.getElementById('actualDateRange').value =
                    selectedDates[0].toISOString().split('T')[0] + ',' +
                    selectedDates[1].toISOString().split('T')[0];
            }
        }
    });
});

