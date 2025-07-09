import {getCookie} from "./utils.js";
// 搜索及初始化操作
document.addEventListener('DOMContentLoaded', function () {
    const faultTableBody = document.getElementById('faultTableBody');
    const searchForm = document.getElementById('searchForm');
    const paginationElement = document.getElementById('pagination');
    const DEFAULT_PAGE_SIZE = 20;
    let currentPage = 1;
    let totalPages = 1;

    function sendSearchRequest(page = 1) {
        // 更新当前页
        currentPage = page;
        // 获取表单数据并转换为对象
        const formData = new FormData(searchForm);
        const pageSizeElement = document.getElementById('pageSizeSelect');
        const pageSizeValue = pageSizeElement ? pageSizeElement.value : DEFAULT_PAGE_SIZE;
        const data = {
            page: currentPage, page_size: pageSizeValue,
        };
        ['trainNumber', 'status', 'searchDateRange', 'parts', 'expiringDays', 'expiredDays'].forEach(field => {
            data[field] = formData.get(field);
        });
        // 清理空字符串参数
        const cleanedData = Object.fromEntries(Object.entries(data).filter(([_, v]) => v !== '' && v !== null && v !== undefined));

        // 发送POST请求
        fetch('/faults/search_fault_data/', {
            method: 'POST', headers: {
                'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken')
            }, body: JSON.stringify(cleanedData)
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
            checkboxCell.innerHTML = `<input type="checkbox" name="selected_ids" value="${item.id}">`;
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
            // 图片列 (缩略图展示)
            const imageCell = document.createElement('td');
            if (item.image_paths && item.image_paths.length > 0) {
                const container = document.createElement('div');
                container.className = 'image-gallery';
                container.style.display = 'flex';
                container.style.flexWrap = 'wrap';
                container.style.gap = '5px';

                item.image_paths.forEach((path, index) => {
                    const fullPath = `${window.MEDIA_URL}${path}`;

                    const imgContainer = document.createElement('div');
                    imgContainer.style.position = 'relative';
                    imgContainer.style.width = '50px';
                    imgContainer.style.height = '50px';

                    const img = document.createElement('img');
                    img.src = fullPath;
                    img.className = 'img-thumbnail';
                    img.style.width = '100%';
                    img.style.height = '100%';
                    img.style.objectFit = 'cover';
                    img.style.cursor = 'pointer';

                    // 添加点击查看大图功能
                    img.addEventListener('click', function () {
                        showLightbox(fullPath, item.id, index, item.image_paths);
                    });

                    // 图片数量指示器
                    if (index === 0 && item.image_paths.length > 1) {
                        const badge = document.createElement('span');
                        badge.className = 'badge bg-primary';
                        badge.style.position = 'absolute';
                        badge.style.top = '-8px';
                        badge.style.right = '-8px';
                        badge.textContent = `+${item.image_paths.length - 1}`;
                        imgContainer.appendChild(badge);
                    }

                    imgContainer.appendChild(img);
                    container.appendChild(imgContainer);
                });

                imageCell.appendChild(container);
            } else {
                imageCell.textContent = '无图片';
            }
            row.appendChild(imageCell);

            // 图片路径列 (隐藏，用于导出)
            const pathCell = document.createElement('td');
            pathCell.style.display = 'none'; // 隐藏列
            pathCell.textContent = item.image_paths ? item.image_paths.join(', ') : '';
            row.appendChild(pathCell);
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

    // 页面加载完成后发送空搜索请求
    sendSearchRequest();

// 搜索按钮事件
    document.getElementById('searchBtn').addEventListener('click', function (event) {
        event.preventDefault();
        sendSearchRequest(1); // 重置到第一页
    });

// 添加删除按钮事件监听
    document.getElementById('deleteBtn').addEventListener('click', function () {
        // 获取所有选中的复选框
        const selectedCheckboxes = document.querySelectorAll('input[name="selected_ids"]:checked');

        if (selectedCheckboxes.length === 0) {
            alert('请至少选择一条要删除的记录！');
            return;
        }

        // 确认删除
        if (!confirm(`确定要删除选中的 ${selectedCheckboxes.length} 条数据吗？此操作不可撤销！`)) {
            return;
        }

        // 收集选中的ID
        const idsToDelete = Array.from(selectedCheckboxes).map(checkbox => checkbox.value);

        // 发送删除请求
        fetch('/faults/delete_faults/', {
            method: 'POST', headers: {
                'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken')
            }, body: JSON.stringify({ids: idsToDelete})
        })
            .then(response => {
                if (!response.ok) {
                    throw new Error('删除请求失败');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    alert(`成功删除 ${data.deleted_count} 条记录！`);
                    // 刷新表格
                    sendSearchRequest(currentPage);
                } else {
                    alert(`删除失败: ${data.message}`);
                }
            })
            .catch(error => {
                console.error('删除错误:', error);
                alert('删除过程中发生错误，请重试');
            });
    });

    // 全选框
    document.getElementById('selectAll').addEventListener('change', function () {
        const checkboxes = document.querySelectorAll('input[name="selected_ids"]');
        checkboxes.forEach(checkbox => {
            checkbox.checked = this.checked;
        });
    });

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
                document.getElementById('actualDateRange').value = selectedDates[0].toISOString().split('T')[0] + ',' + selectedDates[1].toISOString().split('T')[0];
            }
        }
    })

// 修改数据
    document.getElementById('editBtn').addEventListener('click', function () {
        const selectedCheckboxes = document.querySelectorAll('input[name="selected_ids"]:checked');

        if (selectedCheckboxes.length === 0) {
            alert('请选择一条要修改的记录！');
            return;
        }

        if (selectedCheckboxes.length > 1) {
            alert('一次只能修改一条记录！');
            return;
        }

        const recordId = selectedCheckboxes[0].value;
        // 跳转到修改页面并传递记录ID
        window.location.href = `/faults/modify_fault_data.html/?id=${recordId}`;
    });

});

$(document).ready(function () {
    // 导出按钮点击事件
    $('#exportBtn').on('click', function () {
        // 获取表单数据
        const formData = $('#searchForm').serialize();

        // 发送导出请求
        $.ajax({
            url: '/faults/export_fault_records/',
            type: 'POST',
            data: formData,
            headers: {
                'X-CSRFToken': getCookie('csrftoken')  // 获取CSRF令牌
            },
            xhrFields: {
                responseType: 'blob'  // 处理二进制响应
            },
            success: function (blob) {
                // 创建下载链接
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'fault_records_' + new Date().toISOString().slice(0, 10) + '.xlsx';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            },
            error: function (xhr) {
                alert('导出失败: ' + xhr.responseText);
            }
        });
    });
});

// Lightbox显示大图
function showLightbox(src, recordId, index, allPaths) {
    const lightbox = document.getElementById('lightbox');
    const lightboxImg = document.getElementById('lightbox-img');
    const lightboxCounter = document.getElementById('lightbox-counter');
    const lightboxDownload = document.getElementById('lightbox-download');

    if (!lightbox) {
        // 创建lightbox元素
        const lb = document.createElement('div');
        lb.id = 'lightbox';
        lb.style.position = 'fixed';
        lb.style.top = '0';
        lb.style.left = '0';
        lb.style.width = '100%';
        lb.style.height = '100%';
        lb.style.backgroundColor = 'rgba(0,0,0,0.8)';
        lb.style.display = 'flex';
        lb.style.justifyContent = 'center';
        lb.style.alignItems = 'center';
        lb.style.zIndex = '1000';
        lb.style.opacity = '0';
        lb.style.transition = 'opacity 0.3s';
        lb.style.cursor = 'pointer';

        const img = document.createElement('img');
        img.id = 'lightbox-img';
        img.style.maxWidth = '90%';
        img.style.maxHeight = '90%';
        img.style.objectFit = 'contain';

        const counter = document.createElement('div');
        counter.id = 'lightbox-counter';
        counter.style.position = 'absolute';
        counter.style.top = '20px';
        counter.style.left = '20px';
        counter.style.color = 'white';
        counter.style.fontSize = '1.2rem';
        counter.style.backgroundColor = 'rgba(0,0,0,0.5)';
        counter.style.padding = '5px 10px';
        counter.style.borderRadius = '5px';

        const downloadBtn = document.createElement('button');
        downloadBtn.id = 'lightbox-download';
        downloadBtn.className = 'btn btn-sm btn-primary';
        downloadBtn.style.position = 'absolute';
        downloadBtn.style.bottom = '20px';
        downloadBtn.style.right = '20px';
        downloadBtn.innerHTML = '<i class="bi bi-download"></i> 下载';

        lb.appendChild(img);
        lb.appendChild(counter);
        lb.appendChild(downloadBtn);
        document.body.appendChild(lb);

        // 点击关闭lightbox
        lb.addEventListener('click', function (e) {
            if (e.target === lb) {
                lb.style.opacity = '0';
                setTimeout(() => lb.style.display = 'none', 300);
            }
        });
    }

    // 设置当前图片
    lightboxImg.src = src;
    lightboxCounter.textContent = `${index + 1}/${allPaths.length}`;

    // 设置下载链接
    lightboxDownload.onclick = function (e) {
        e.stopPropagation();
        const link = document.createElement('a');
        link.href = src;
        link.download = `故障记录_${recordId}_图片${index + 1}.${src.split('.').pop()}`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    // 显示lightbox
    lightbox.style.display = 'flex';
    setTimeout(() => lightbox.style.opacity = '1', 10);

    // 如果有多张图片，添加导航按钮
    if (allPaths.length > 1) {
        // 添加左箭头
        if (!document.getElementById('lightbox-prev')) {
            const prevBtn = document.createElement('button');
            prevBtn.id = 'lightbox-prev';
            prevBtn.className = 'btn btn-light';
            prevBtn.style.position = 'absolute';
            prevBtn.style.left = '20px';
            prevBtn.style.top = '50%';
            prevBtn.style.transform = 'translateY(-50%)';
            prevBtn.innerHTML = '<i class="bi bi-chevron-left"></i>';
            prevBtn.style.fontSize = '2rem';
            prevBtn.style.zIndex = '1001';

            prevBtn.addEventListener('click', function (e) {
                e.stopPropagation();
                const newIndex = (index - 1 + allPaths.length) % allPaths.length;
                showLightbox(`${window.MEDIA_URL}${allPaths[newIndex]}`, recordId, newIndex, allPaths);
            });

            lightbox.appendChild(prevBtn);
        }

        // 添加右箭头
        if (!document.getElementById('lightbox-next')) {
            const nextBtn = document.createElement('button');
            nextBtn.id = 'lightbox-next';
            nextBtn.className = 'btn btn-light';
            nextBtn.style.position = 'absolute';
            nextBtn.style.right = '20px';
            nextBtn.style.top = '50%';
            nextBtn.style.transform = 'translateY(-50%)';
            nextBtn.innerHTML = '<i class="bi bi-chevron-right"></i>';
            nextBtn.style.fontSize = '2rem';
            nextBtn.style.zIndex = '1001';

            nextBtn.addEventListener('click', function (e) {
                e.stopPropagation();
                const newIndex = (index + 1) % allPaths.length;
                showLightbox(`${window.MEDIA_URL}${allPaths[newIndex]}`, recordId, newIndex, allPaths);
            });

            lightbox.appendChild(nextBtn);
        }
    }
}






