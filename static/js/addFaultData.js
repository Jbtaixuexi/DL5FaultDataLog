// 在页面加载完成后执行
document.addEventListener('DOMContentLoaded', function () {
    const vehicleSelect = document.getElementById('车号');
    const apiUrl = '/faults/getVehicles/'; // 根据实际URL配置调整

    // 发送GET请求获取车号列表
    fetch(apiUrl)
        .then(response => response.json())
        .then(vehicles => {
            // 清空原有选项（除了第一个"请选择车号"）
            while (vehicleSelect.options.length > 1) {
                vehicleSelect.remove(1);
            }

            // 添加从数据库获取的车号选项
            vehicles.forEach(plateNumber => {
                const option = document.createElement('option');
                option.value = plateNumber;
                option.textContent = plateNumber;
                vehicleSelect.appendChild(option);
            });
        })
        .catch(error => {
            console.error('获取车号列表失败:', error);
            // 可以在这里添加错误提示
        });
});


// 添加默认数据
$(document).ready(function () {
    // 设置默认日期和时间
    const now = new Date();
    const dateStr = now.toISOString().split('T')[0];
    const timeStr = now.toTimeString().substring(0, 5);

    $('#日期').val(dateStr);
    $('#时间').val(timeStr);
    $('#登记时间').val(dateStr);

    // 设置默认用户信息
    $('#报告人').val(currentUser.username);
    $('#跟进技术人员').val(currentUser.username);
    $('#登记人').val(currentUser.username);

    // 加载受理人列表（level 1和2的用户）
    $.ajax({
        url: 'accepted_list/',
        type: 'GET',
        success: function (data) {
            const accepterSelect = $('#受理人');
            data.forEach(user => {
                accepterSelect.append(`<option value="${user.username}">${user.username}</option>`);
            });
        }
    });

    // 是否更换备件事件监听
    $('#是否更换备件').change(function () {
        if ($(this).val() === '是') {
            $('#partDetailsGroup').show();
        } else {
            $('#partDetailsGroup').hide();
        }
    });

    // 图片上传数量变化事件监听
    $('#imageCount').change(function () {
        const count = parseInt($(this).val());
        const container = $('#uploadFields');
        container.empty();

        if (count > 0) {
            $('#imageUploadContainer').show();
            for (let i = 1; i <= count; i++) {
                container.append(`
                    <div class="mb-3">
                        <label for="image_${i}" class="form-label">图片 ${i}</label>
                        <input type="file" class="form-control" id="image_${i}" 
                               name="image_${i}" accept="image/*">
                    </div>
                `);
            }
        } else {
            $('#imageUploadContainer').hide();
        }
    });

    // 表单提交处理
    $('#addForm').submit(function (e) {
        e.preventDefault();

        const formData = new FormData(this);

        // 添加当前用户信息
        formData.append('registrar', currentUser.username);

        $.ajax({
            url: '/faults/add_fault_data/',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function (response) {
                if (response.success) {
                    $('#addResult').removeClass('alert-danger')
                        .addClass('alert-success')
                        .text('故障记录添加成功！')
                        .show();

                    // 重置表单
                    $('#addForm')[0].reset();
                    $('#imageCount').val('0').trigger('change');

                    // 通知受理人
                    notifyAccepter(response.accepter, response.fault_id);
                } else {
                    $('#addResult').removeClass('alert-success')
                        .addClass('alert-danger')
                        .text('添加失败: ' + response.message)
                        .show();
                }
            },
            error: function () {
                $('#addResult').removeClass('alert-success')
                    .addClass('alert-danger')
                    .text('服务器错误，请稍后再试')
                    .show();
            }
        });
    });
});

// 通知受理人函数
function notifyAccepter(accepter, faultId) {
    $.ajax({
        url: '/api/notify-accepter/',
        type: 'POST',
        data: {
            accepter: accepter,
            fault_id: faultId,
            message: `您有一条新的故障记录待处理，ID: ${faultId}`
        },
        success: function (response) {
            console.log('通知已发送');
        }
    });
}


document.addEventListener('DOMContentLoaded', function () {
    const vehicleSelect = document.getElementById('车号');
    const apiUrl = '/faults/getVehicles/';

    // 获取分类选择器元素
    const systemSelect = document.getElementById('故障系统');
    const secondarySelect = document.getElementById('故障二级分类');
    const thirdSelect = document.getElementById('三级分类');
    const fourthSelect = document.getElementById('四级分类');

    // 加载所有分类数据
    Promise.all([
        fetch('/faults/get-systems/').then(r => r.json()),
        fetch('/faults/get-all-categories/').then(r => r.json())
    ]).then(([systems, categories]) => {
        // 填充车号
        populateVehicleSelect(vehicleSelect, systems.vehicles);

        // 填充一级分类（系统）
        populateSystemSelect(systemSelect, systems.systems);

        // 存储所有分类数据用于级联选择
        window.allCategories = categories;

        // 设置分类选择事件监听
        setupCategoryListeners(systemSelect, secondarySelect, thirdSelect, fourthSelect);
    }).catch(error => {
        console.error('初始化失败:', error);
    });

    // 填充车号选择器
    function populateVehicleSelect(select, vehicles) {
        while (select.options.length > 1) {
            select.remove(1);
        }
        vehicles.forEach(vehicle => {
            const option = document.createElement('option');
            option.value = vehicle.id;
            option.textContent = vehicle.plate_number;
            select.appendChild(option);
        });
    }

    // 填充系统选择器
    function populateSystemSelect(select, systems) {
        systems.forEach(system => {
            const option = document.createElement('option');
            option.value = system.id;
            option.textContent = system.name;
            select.appendChild(option);
        });
    }

    // 设置分类选择器事件监听
    function setupCategoryListeners(systemSelect, secondarySelect, thirdSelect, fourthSelect) {
        // 一级分类变化时更新二级分类
        systemSelect.addEventListener('change', function() {
            const systemId = this.value;
            populateSecondarySelect(secondarySelect, systemId);

            // 重置下级分类
            resetSelect(thirdSelect);
            resetSelect(fourthSelect);
        });

        // 二级分类变化时更新三级分类
        secondarySelect.addEventListener('change', function() {
            const secondaryId = this.value;
            populateThirdSelect(thirdSelect, secondaryId);

            // 重置下级分类
            resetSelect(fourthSelect);
        });

        // 三级分类变化时更新四级分类
        thirdSelect.addEventListener('change', function() {
            const thirdId = this.value;
            populateFourthSelect(fourthSelect, thirdId);
        });
    }

    // 填充二级分类选择器
    function populateSecondarySelect(select, systemId) {
        resetSelect(select);

        if (!systemId) return;

        const secondaries = window.allCategories.secondaries.filter(
            sec => sec.system_id == systemId
        );

        secondaries.forEach(sec => {
            const option = document.createElement('option');
            option.value = sec.id;
            option.textContent = sec.name;
            select.appendChild(option);
        });
    }

    // 填充三级分类选择器
    function populateThirdSelect(select, secondaryId) {
        resetSelect(select);

        if (!secondaryId) return;

        const thirds = window.allCategories.thirds.filter(
            third => third.secondary_id == secondaryId
        );

        thirds.forEach(third => {
            const option = document.createElement('option');
            option.value = third.id;
            option.textContent = third.name;
            select.appendChild(option);
        });
    }

    // 填充四级分类选择器
    function populateFourthSelect(select, thirdId) {
        resetSelect(select);

        if (!thirdId) return;

        const fourths = window.allCategories.fourths.filter(
            fourth => fourth.third_id == thirdId
        );

        fourths.forEach(fourth => {
            const option = document.createElement('option');
            option.value = fourth.id;
            option.textContent = fourth.name;
            select.appendChild(option);
        });
    }

    // 重置选择器（保留第一个选项）
    function resetSelect(select) {
        while (select.options.length > 1) {
            select.remove(1);
        }
        select.value = "";
    }
});