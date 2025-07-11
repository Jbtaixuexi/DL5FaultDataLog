document.addEventListener('DOMContentLoaded', function () {
    // 从URL获取记录ID
    const urlParams = new URLSearchParams(window.location.search);
    const recordId = urlParams.get('id');

    if (!recordId) {
        alert('未找到记录ID');
        window.location.href = '/faults/search_fault_data/';
        return;
    }

    // 设置修改人和修改时间
    const now = new Date();
    document.getElementById('修改时间').value = now.toISOString().slice(0, 16);     // YYYY-MM-DDTHH:mm
    document.getElementById('修改人').value = currentUser.username;

    // 获取记录数据
    fetch(`/faults/get_fault_record/?id=${recordId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                populateForm(data.record);
                initDropdowns(data.record);
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error('获取记录失败:', error);
            alert('获取记录失败');
        });

    // 表单提交处理
    document.getElementById('modifyForm').addEventListener('submit', function (e) {
        e.preventDefault();
        saveChanges();
    });

    // 取消按钮事件
    document.getElementById('cancelBtn').addEventListener('click', function () {
        window.location.href = '/faults/search_fault_data/';
    });

    // 是否更换备件事件监听
    document.getElementById('是否更换备件').addEventListener('change', function () {
        const partDetailsGroup = document.getElementById('partDetailsGroup');
        if (this.value === '是') {
            partDetailsGroup.style.display = 'block';
        } else {
            partDetailsGroup.style.display = 'none';
        }
    });
});

// 填充表单数据
// 填充表单数据
function populateForm(record) {
    // 设置记录ID
    document.getElementById('recordId').value = record.id;

    // 基本信息
    document.getElementById('日期').value = record.date || '';
    document.getElementById('时间').value = record.time || '';
    document.getElementById('问题来源').value = record.source || '';
    document.getElementById('故障类别').value = record.fault_type || '';
    document.getElementById('故障现象').value = record.phenomenon || '';
    document.getElementById('故障具体位置').value = record.location || '';

    // 状态字段处理 - 英文转中文
    const statusMapping = {
        'pending': '待处理',
        'processing': '处理中',
        'resolved': '已解决'
    };
    document.getElementById('状态').value = statusMapping[record.status] || '待处理';

    // 处理信息
    document.getElementById('跟进技术人员').value = record.technician || '';
    document.getElementById('故障原因').value = record.cause || '';
    document.getElementById('报告人').value = record.reporter || '';
    document.getElementById('受理人').value = record.receiver || '';
    document.getElementById('当前进度').value = record.progress || '';

    if (record.expected_date) {
        document.getElementById('预计处理日期').value = record.expected_date.split('T')[0];
    }

    document.getElementById('处理办法').value = record.solution || '';
    document.getElementById('是否更换备件').value = record.part_replaced ? '是' : '否';

    // 备件信息
    if (record.part_replaced) {
        document.getElementById('更换备件名称').value = record.part_name || '';
        document.getElementById('更换数量').value = record.part_quantity || '';
        document.getElementById('辅料').value = record.materials || '';
        document.getElementById('工具').value = record.tools || '';
        document.getElementById('partDetailsGroup').style.display = 'block';
    } else {
        document.getElementById('partDetailsGroup').style.display = 'none';
    }

    document.getElementById('故障定位用时(分钟)').value = record.location_time || '';
    document.getElementById('更换用时(分钟)').value = record.replacement_time || '';

    if (record.legacy_date) {
        document.getElementById('遗留项处理日期').value = record.legacy_date.split('T')[0];
    }

    // 登记信息
    document.getElementById('登记人').value = record.registrar || '';

    if (record.registration_time) {
        const regTime = new Date(record.registration_time);
        document.getElementById('登记时间').value = regTime.toISOString().slice(0, 16);
    }

    document.getElementById('是否有效').value = record.is_valid ? '是' : '否';

    // 图片信息
    const imageInfo = document.getElementById('imageInfo');
    if (record.image_count > 0) {
        imageInfo.textContent = `已有 ${record.image_count} 张图片`;
    } else {
        imageInfo.textContent = '没有图片';
    }
}

// 初始化下拉框
function initDropdowns(record) {
    // 加载车号列表
    fetch('/faults/getVehicles/')
        .then(response => response.json())
        .then(vehicles => {
            const vehicleSelect = document.getElementById('车号');
            vehicles.forEach(vehicle => {

                const option = document.createElement('option');
                option.value = vehicle;
                option.textContent = vehicle;
                vehicleSelect.appendChild(option);
            });
            vehicleSelect.value = record.train_number || '';
        });

    // 加载受理人列表
    fetch('/faults/accepted_list/')
        .then(response => response.json())
        .then(accepters => {
            const accepterSelect = document.getElementById('受理人');
            accepters.forEach(accepter => {
                const option = document.createElement('option');
                option.value = accepter.username;
                option.textContent = accepter.username;
                accepterSelect.appendChild(option);
            });
            accepterSelect.value = record.receiver || '';
        });

    // 加载分类系统
    loadClassificationSystems(record);
}

// 加载分类系统（修改后）
function loadClassificationSystems(record) {
    Promise.all([
        fetch('/faults/get_systems/').then(r => r.json()),
        fetch('/faults/get_all_categories/').then(r => r.json())
    ]).then(([systemsData, categoriesData]) => {
        const systemSelect = document.getElementById('故障系统');
        const secondarySelect = document.getElementById('故障二级分类');
        const thirdSelect = document.getElementById('三级分类');
        const fourthSelect = document.getElementById('四级分类');

        // 清空下拉菜单
        systemSelect.innerHTML = '<option value="">请选择故障系统</option>';
        secondarySelect.innerHTML = '<option value="">请选择二级分类</option>';
        thirdSelect.innerHTML = '<option value="">请选择三级分类</option>';
        fourthSelect.innerHTML = '<option value="">请选择四级分类</option>';

        // 填充系统选项
        systemsData.systems.forEach(system => {
            const option = new Option(system.name, system.id);
            systemSelect.add(option);
        });

        // 填充所有二级分类
        categoriesData.secondaries.forEach(sec => {
            const option = new Option(sec.name, sec.id);
            option.dataset.systemId = sec.system_id; // 存储系统关联
            secondarySelect.add(option);
        });

        // 填充所有三级分类
        categoriesData.thirds.forEach(third => {
            const option = new Option(third.name, third.id);
            option.dataset.secondaryId = third.secondary_id; // 存储二级关联
            thirdSelect.add(option);
        });

        // 填充所有四级分类
        categoriesData.fourths.forEach(fourth => {
            const option = new Option(fourth.name, fourth.id);
            option.dataset.thirdId = fourth.third_id; // 存储三级关联
            fourthSelect.add(option);
        });

        // 设置当前记录的值
        if (record.system_id) {
            systemSelect.value = record.system_id;
        }
        if (record.secondary_id) {
            secondarySelect.value = record.secondary_id;
        }
        if (record.third_id) {
            thirdSelect.value = record.third_id;
        }
        if (record.fourth_id) {
            fourthSelect.value = record.fourth_id;
        }

        // 绑定change事件 - 使用filter而不是重新获取
        systemSelect.addEventListener('change', function() {
            filterSecondaryBySystem(this.value);
        });

        secondarySelect.addEventListener('change', function() {
            filterThirdBySecondary(this.value);
        });

        thirdSelect.addEventListener('change', function() {
            filterFourthByThird(this.value);
        });
    });
}

// 根据系统筛选二级分类
function filterSecondaryBySystem(systemId) {
    const secondarySelect = document.getElementById('故障二级分类');
    const thirdSelect = document.getElementById('三级分类');
    const fourthSelect = document.getElementById('四级分类');

    // 重置下级菜单
    thirdSelect.value = '';
    fourthSelect.value = '';

    // 显示所有选项
    for (let i = 0; i < secondarySelect.options.length; i++) {
        const option = secondarySelect.options[i];
        option.style.display = 'block';

        // 根据系统ID过滤
        if (systemId && option.value) {
            option.style.display = option.dataset.systemId === systemId ? 'block' : 'none';
        }
    }

    // 自动选择第一个可见选项（如果有）
    for (let i = 0; i < secondarySelect.options.length; i++) {
        if (secondarySelect.options[i].style.display === 'block' && secondarySelect.options[i].value) {
            secondarySelect.value = secondarySelect.options[i].value;
            secondarySelect.dispatchEvent(new Event('change'));
            break;
        }
    }
}

// 根据二级分类筛选三级分类
function filterThirdBySecondary(secondaryId) {
    const thirdSelect = document.getElementById('三级分类');
    const fourthSelect = document.getElementById('四级分类');

    // 重置下级菜单
    fourthSelect.value = '';

    // 显示所有选项
    for (let i = 0; i < thirdSelect.options.length; i++) {
        const option = thirdSelect.options[i];
        option.style.display = 'block';

        // 根据二级ID过滤
        if (secondaryId && option.value) {
            option.style.display = option.dataset.secondaryId === secondaryId ? 'block' : 'none';
        }
    }

    // 自动选择第一个可见选项（如果有）
    for (let i = 0; i < thirdSelect.options.length; i++) {
        if (thirdSelect.options[i].style.display === 'block' && thirdSelect.options[i].value) {
            thirdSelect.value = thirdSelect.options[i].value;
            thirdSelect.dispatchEvent(new Event('change'));
            break;
        }
    }
}

// 根据三级分类筛选四级分类
function filterFourthByThird(thirdId) {
    const fourthSelect = document.getElementById('四级分类');

    // 显示所有选项
    for (let i = 0; i < fourthSelect.options.length; i++) {
        const option = fourthSelect.options[i];
        option.style.display = 'block';

        // 根据三级ID过滤
        if (thirdId && option.value) {
            option.style.display = option.dataset.thirdId === thirdId ? 'block' : 'none';
        }
    }

    // 自动选择第一个可见选项（如果有）
    for (let i = 0; i < fourthSelect.options.length; i++) {
        if (fourthSelect.options[i].style.display === 'block' && fourthSelect.options[i].value) {
            fourthSelect.value = fourthSelect.options[i].value;
            break;
        }
    }
}
// 保存修改
function saveChanges() {
    const form = document.getElementById('modifyForm');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());

    // 发送更新请求
    fetch('/faults/update_fault_record/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify(data)
    })
        .then(response => response.json())
        .then(result => {
            const resultDiv = document.getElementById('modifyResult');
            resultDiv.style.display = 'block';

            if (result.success) {
                resultDiv.className = 'alert alert-success';
                resultDiv.textContent = '修改成功！';

                // 3秒后跳回搜索页面
                setTimeout(() => {
                    window.location.href = '/faults/search_fault_data/';
                }, 3000);
            } else {
                resultDiv.className = 'alert alert-danger';
                resultDiv.textContent = `修改失败: ${result.message}`;
            }
        })
        .catch(error => {
            console.error('保存失败:', error);
            const resultDiv = document.getElementById('modifyResult');
            resultDiv.style.display = 'block';
            resultDiv.className = 'alert alert-danger';
            resultDiv.textContent = '保存失败，请重试';
        });
}

// 获取CSRF token
function getCSRFToken() {
    const cookieValue = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrftoken='))
        ?.split('=')[1];
    return cookieValue || '';
}