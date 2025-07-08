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
    const dateTimeStr = now.toISOString().slice(0, 16); // YYYY-MM-DDTHH:mm
    document.getElementById('修改时间').value = dateTimeStr;
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
    document.getElementById('车号').value = record.train_number || '';
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
    const statusValue = statusMapping[record.status] || '待处理';
    document.getElementById('状态').value = statusValue;

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

// 加载分类系统
function loadClassificationSystems(record) {
    Promise.all([
        fetch('/faults/get-systems/').then(r => r.json()),
        fetch('/faults/get-all-categories/').then(r => r.json())
    ]).then(([systemsData, categoriesData]) => {
        const systemSelect = document.getElementById('故障系统');
        const secondarySelect = document.getElementById('故障二级分类');
        const thirdSelect = document.getElementById('三级分类');
        const fourthSelect = document.getElementById('四级分类');


        // 填充系统
        systemsData.systems.forEach(system => {
            const option = document.createElement('option');
            option.value = system.id;
            option.textContent = system.name;
            systemSelect.appendChild(option);
        });

        // 设置当前记录的系统
        if (record.system_name) {
            const systemOption = [...systemSelect.options].find(
                opt => opt.text === record.system_name
            );
            if (systemOption) systemSelect.value = systemOption.value;
        }

        // 填充二级分类
        if (record.system_name) {
            const systemId = [...systemSelect.options].find(
                opt => opt.text === record.system_name
            )?.value;

            if (systemId) {
                const secondaries = categoriesData.secondaries.filter(
                    sec => sec.system_id === systemId
                );

                secondaries.forEach(sec => {
                    const option = document.createElement('option');
                    option.value = sec.id;
                    option.textContent = sec.name;
                    secondarySelect.appendChild(option);
                });
            }
        }

        // 设置当前记录的二级分类
        if (record.secondary_name) {
            const secondaryOption = [...secondarySelect.options].find(
                opt => opt.text === record.secondary_name
            );
            if (secondaryOption) secondarySelect.value = secondaryOption.value;
        }

        // 填充三级分类
        if (record.secondary_name) {
            const secondaryId = [...secondarySelect.options].find(
                opt => opt.text === record.secondary_name
            )?.value;

            if (secondaryId) {
                const thirds = categoriesData.thirds.filter(
                    third => third.secondary_id === secondaryId
                );

                thirds.forEach(third => {
                    const option = document.createElement('option');
                    option.value = third.id;
                    option.textContent = third.name;
                    thirdSelect.appendChild(option);
                });
            }
        }

        // 设置当前记录的三级分类
        if (record.third_name) {
            const thirdOption = [...thirdSelect.options].find(
                opt => opt.text === record.third_name
            );
            if (thirdOption) thirdSelect.value = thirdOption.value;
        }

        // 填充四级分类
        if (record.third_name) {
            const thirdId = [...thirdSelect.options].find(
                opt => opt.text === record.third_name
            )?.value;

            if (thirdId) {
                const fourths = categoriesData.fourths.filter(
                    fourth => fourth.third_id === thirdId
                );

                fourths.forEach(fourth => {
                    const option = document.createElement('option');
                    option.value = fourth.id;
                    option.textContent = fourth.name;
                    fourthSelect.appendChild(option);
                });
            }
        }

        // 设置当前记录的四级分类
        if (record.fourth_name) {
            const fourthOption = [...fourthSelect.options].find(
                opt => opt.text === record.fourth_name
            );
            if (fourthOption) fourthSelect.value = fourthOption.value;
        }
    });
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