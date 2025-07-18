import {loadClassificationSystems} from './utils.js';

// 在文件顶部添加全局变量
let currentRecordId = null;
let existingImagePaths = [];
const maxNewImages = 5;
let newImageCount = 0;
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

    // 添加新图片按钮事件
    document.getElementById('addNewImageBtn').addEventListener('click', function () {
        if (newImageCount >= maxNewImages) {
            alert(`最多只能添加${maxNewImages}张新图片`);
            return;
        }

        newImageCount++;
        document.getElementById('newImageCount').value = newImageCount;

        const fieldDiv = document.createElement('div');
        fieldDiv.className = 'upload-field mb-2';
        fieldDiv.innerHTML = `
            <div class="input-group">
                <input type="file" class="form-control" name="new_image_${newImageCount}" 
                       accept="image/jpeg, image/png" data-index="${newImageCount}">
                <button type="button" class="btn btn-outline-danger delete-new-image-btn">删除</button>
            </div>
            <div class="image-preview mt-2" id="new_preview_${newImageCount}" style="display:none;">
                <img src="" alt="预览" style="max-width:100px; max-height:100px;">
            </div>
        `;

        document.getElementById('newUploadFields').appendChild(fieldDiv);

        // 添加删除按钮事件
        fieldDiv.querySelector('.delete-new-image-btn').addEventListener('click', function () {
            fieldDiv.remove();
            newImageCount--;
            document.getElementById('newImageCount').value = newImageCount;
        });

        // 添加文件选择事件
        const fileInput = fieldDiv.querySelector('input[type="file"]');
        fileInput.addEventListener('change', function (e) {
            const previewDiv = document.getElementById(`new_preview_${this.dataset.index}`);
            if (this.files && this.files[0]) {
                const reader = new FileReader();
                reader.onload = function (e) {
                    previewDiv.style.display = 'block';
                    previewDiv.querySelector('img').src = e.target.result;
                }
                reader.readAsDataURL(this.files[0]);
            } else {
                previewDiv.style.display = 'none';
            }
        });
    });
});

// 填充表单数据
function populateForm(record) {
    currentRecordId = record.id;
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
    existingImagePaths = record.image_paths || [];
    renderExistingImages();

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


// 保存修改
async function saveChanges() {
    const form = document.getElementById('modifyForm');
    const formData = new FormData(form);

    // 添加新图片
    const newImageInputs = document.querySelectorAll('#newUploadFields input[type="file"]');
    const newImages = [];

    for (const input of newImageInputs) {
        if (input.files.length > 0) {
            newImages.push(input.files[0]);
        }
    }

    // 添加新图片到 FormData
    newImages.forEach((image, index) => {
        formData.append('new_images', image);
    });

    // 添加记录ID
    formData.append('recordId', currentRecordId);

    try {
        const response = await fetch('/faults/update_fault_record/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });

        const result = await response.json();
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
    } catch (error) {
        console.error('保存失败:', error);
        const resultDiv = document.getElementById('modifyResult');
        resultDiv.style.display = 'block';
        resultDiv.className = 'alert alert-danger';
        resultDiv.textContent = '保存失败，请重试';
    }
}


// 提取图片渲染为单独函数
function renderExistingImages() {
    const imageInfo = document.getElementById('imageInfo');
    const existingImagesDiv = document.getElementById('existingImages');

    if (existingImagePaths.length > 0) {
        imageInfo.textContent = `已有 ${existingImagePaths.length} 张图片`;
        existingImagesDiv.innerHTML = '';

        existingImagePaths.forEach((path, index) => {
            const imgContainer = document.createElement('div');
            imgContainer.className = 'image-thumbnail-container position-relative d-inline-block';

            const img = document.createElement('img');
            img.src = `/media/${path}`;
            img.alt = `图片${index + 1}`;
            img.className = 'img-thumbnail';
            img.style.width = '100px';
            img.style.height = '100px';
            img.style.objectFit = 'cover';

            const deleteBtn = document.createElement('button');
            deleteBtn.type = 'button';
            deleteBtn.className = 'btn btn-sm btn-danger delete-image-btn position-absolute top-0 end-0';
            deleteBtn.innerHTML = '&times;';
            deleteBtn.onclick = function () {
                deleteImage(path);
            };

            imgContainer.appendChild(img);
            imgContainer.appendChild(deleteBtn);
            existingImagesDiv.appendChild(imgContainer);
        });
    } else {
        imageInfo.textContent = '没有图片';
        existingImagesDiv.innerHTML = '';
    }
}

function deleteImage(imagePath) {
    if (!confirm('确定要删除这张照片吗？')) return;

    fetch('/faults/delete_image/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCSRFToken()
        },
        body: JSON.stringify({
            record_id: currentRecordId,
            image_path: imagePath
        })
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 从现有图片路径中移除
                existingImagePaths = existingImagePaths.filter(path => path !== imagePath);
                // 重新渲染图片
                renderExistingImages();
                alert('图片已删除');
            } else {
                alert('删除失败: ' + data.message);
            }
        })
        .catch(error => {
            console.error('删除图片失败:', error);
            alert('删除图片失败');
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