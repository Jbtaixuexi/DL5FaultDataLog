export function getCookie(name) {
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


// 加载分类系统（修改后）
export function loadClassificationSystems(record) {

    // 处理未传入record的情况：默认为空对象
    record = record || {};

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
        // 设置当前记录的值（安全访问属性）
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
        systemSelect.addEventListener('change', function () {
            filterSecondaryBySystem(this.value);
        });

        secondarySelect.addEventListener('change', function () {
            filterThirdBySecondary(this.value);
        });

        thirdSelect.addEventListener('change', function () {
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