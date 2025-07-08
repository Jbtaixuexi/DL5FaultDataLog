import os
import uuid
from django.http import FileResponse
from django.utils.encoding import escape_uri_path
import pandas as pd
from django.conf import settings
from django.core.paginator import Paginator
from django.forms import model_to_dict
from accounts.models import CustomUser
from datetime import datetime, timedelta, date
from django.db.models import Q
from django.shortcuts import render
from django.views.decorators.http import require_http_methods, require_GET, require_POST
import logging
import json
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .models import FaultRecord, System, SecondaryCategory, ThirdCategory, FourthCategory, Vehicle

logger = logging.getLogger(__name__)


# 查询用法
@require_http_methods(['GET', 'POST'])
def search_fault_data(request):
    if request.method == 'GET':
        return render(request, 'searchFaultData.html')
    else:
        try:
            # 记录原始请求数据
            raw_data = request.body.decode('utf-8')
            logger.info(f"Received search request: {raw_data}")

            # 解析请求数据
            data = json.loads(request.body)
            logger.info(f"Parsed data: {data}")
            page = data.get('page', 1)
            train_number = data.get('trainNumber', '').strip()
            status = data.get('status', '')
            date_range_str = data.get('searchDateRange', '')
            parts = data.get('parts', '').strip()
            expiring_days = data.get('expiringDays', '') or None
            expired_days = data.get('expiredDays', '') or None
            page_size = int(data.get('page_size'))

            # 转换数字参数
            if expiring_days is not None:
                try:
                    expiring_days = int(expiring_days)
                except (ValueError, TypeError):
                    expiring_days = None
                    logger.warning(f"Invalid expiringDays: {data.get('expiringDays')}")

            if expired_days is not None:
                try:
                    expired_days = int(expired_days)
                except (ValueError, TypeError):
                    expired_days = None
                    logger.warning(f"Invalid expiredDays: {data.get('expiredDays')}")

            # 构建查询条件 - 添加 select_related 优化外键查询
            queryset = FaultRecord.objects.select_related(
                'system', 'secondary', 'third', 'fourth'
            ).all()

            logger.info(f"Initial queryset count: {queryset.count()}")

            if train_number:
                queryset = queryset.filter(train_number__icontains=train_number)
                logger.info(f"After train_number filter: {queryset.count()}")

            if status:
                # 状态映射
                status_map = {'待处理': 'pending', '处理中': 'processing', '已解决': 'resolved'}
                status_value = status_map.get(status, '')
                if status_value:
                    queryset = queryset.filter(status=status_value)
                    logger.info(f"After status filter: {queryset.count()}")

            if date_range_str:
                try:
                    if '至' in date_range_str:
                        start_str, end_str = [s.strip() for s in date_range_str.split('至')]
                    else:
                        start_str, end_str = date_range_str.split(',')
                    start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
                    end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
                    queryset = queryset.filter(date__range=[start_date, end_date])
                    logger.info(f"After date filter: {queryset.count()}")
                except Exception as e:
                    logger.warning(f"日期数据格式不正确: {date_range_str} - {str(e)}")

            # 按部件名称过滤
            if parts:
                queryset = queryset.filter(
                    Q(system__name__icontains=parts) |
                    Q(secondary__name__icontains=parts) |
                    Q(third__name__icontains=parts) |
                    Q(fourth__name__icontains=parts)
                )
                logger.info(f"After parts filter: {queryset.count()}")

            # 处理临期和过期天数
            today = datetime.now().date()
            if expiring_days is not None:
                expiration_date = today + timedelta(days=expiring_days)
                queryset = queryset.filter(
                    expected_date__isnull=False,
                    expected_date__lte=expiration_date,
                    expected_date__gte=today
                )
                logger.info(f"After expiring filter: {queryset.count()}")

            if expired_days is not None:
                expiration_date = today - timedelta(days=expired_days)
                queryset = queryset.filter(
                    expected_date__isnull=False,
                    expected_date__lt=today,
                    expected_date__gte=expiration_date
                )
                logger.info(f"After expired filter: {queryset.count()}")

            # 排序和分页
            queryset = queryset.order_by('-date', '-time')
            paginator = Paginator(queryset, page_size)
            page_obj = paginator.get_page(page)

            # 构建响应数据
            records = []

            for record in page_obj:
                # 使用 model_to_dict 获取所有字段
                record_data = model_to_dict(record)

                # 替换分类ID为分类名称
                record_data['system'] = record.system.name if record.system else None
                record_data['secondary'] = record.secondary.name if record.secondary else None
                record_data['third'] = record.third.name if record.third else None
                record_data['fourth'] = record.fourth.name if record.fourth else None

                # 格式化日期时间字段
                record_data['date'] = record.date.strftime('%Y-%m-%d') if record.date else None
                record_data['time'] = record.time.strftime('%H:%M:%S') if record.time else None
                record_data['expected_date'] = record.expected_date.strftime(
                    '%Y-%m-%d') if record.expected_date else None
                record_data['legacy_date'] = record.legacy_date.strftime('%Y-%m-%d') if record.legacy_date else None
                record_data['registration_time'] = record.registration_time.strftime(
                    '%Y-%m-%d %H:%M:%S') if record.registration_time else None
                record_data['modified_at'] = record.modified_at.strftime(
                    '%Y-%m-%d %H:%M:%S') if record.modified_at else None

                # 处理状态显示
                record_data['status'] = record.get_status_display()

                # 处理布尔字段
                record_data['part_replaced'] = "是" if record.part_replaced else "否"
                record_data['is_valid'] = "是" if record.is_valid else "否"

                # 添加图片路径信息
                record_data['image_paths'] = record.image_paths
                records.append(record_data)

            logger.info(f"Returning {len(records)} records")

            return JsonResponse({
                'total': paginator.count,
                'page': page_obj.number,
                'total_pages': paginator.num_pages,
                'records': records
            })

        except Exception as e:
            logger.error(f"Error in search_fault_data: {str(e)}", exc_info=True)
            return JsonResponse({'error': 'Internal server error', 'details': str(e)}, status=500)


@require_POST
def export_fault_records(request):
    # 解析请求数据
    params = request.POST.dict()
    train_number = params.get('trainNumber', '').strip()
    status = params.get('status', '')
    date_range_str = params.get('searchDateRange', '')
    parts = params.get('parts', '').strip()
    expiring_days = params.get('expiringDays', '')
    expired_days = params.get('expiredDays', '')

    # 初始化查询集
    queryset = FaultRecord.objects.select_related(
        'system', 'secondary', 'third', 'fourth'
    ).filter()

    logger.info(f"初始查询集记录数: {queryset.count()}")

    # 车号过滤
    if train_number:
        queryset = queryset.filter(train_number__icontains=train_number)
        logger.info(f"车号过滤后记录数: {queryset.count()}")

    # 状态过滤
    if status:
        status_map = {'待处理': 'pending', '处理中': 'processing', '已解决': 'resolved'}
        status_value = status_map.get(status, '')
        if status_value:
            queryset = queryset.filter(status=status_value)
            logger.info(f"状态过滤后记录数: {queryset.count()}")

    # 日期范围过滤
    if date_range_str:
        try:
            # 支持多种分隔符
            if ' to ' in date_range_str:
                start_str, end_str = date_range_str.split(' to ')
            elif '至' in date_range_str:
                start_str, end_str = date_range_str.split('至')
            elif ',' in date_range_str:
                start_str, end_str = date_range_str.split(',')
            else:
                raise ValueError("无效的日期范围格式")

            start_date = datetime.strptime(start_str.strip(), '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str.strip(), '%Y-%m-%d').date()
            queryset = queryset.filter(date__range=[start_date, end_date])
            logger.info(f"日期范围过滤后记录数: {queryset.count()}")
        except Exception as e:
            logger.error(f"日期解析错误: {date_range_str} - {str(e)}")
            # 可以选择不应用日期过滤而不是中断

    # 部件过滤
    if parts:
        queryset = queryset.filter(
            Q(part_name__icontains=parts) |
            Q(system__name__icontains=parts) |
            Q(secondary__name__icontains=parts) |
            Q(third__name__icontains=parts) |
            Q(fourth__name__icontains=parts)
        )
        logger.info(f"部件过滤后记录数: {queryset.count()}")

    # 临期天数过滤
    today = date.today()
    if expiring_days and expiring_days.isdigit():
        expiration_date = today + timedelta(days=int(expiring_days))
        queryset = queryset.filter(
            expected_date__isnull=False,
            expected_date__lte=expiration_date,
            expected_date__gte=today
        )
        logger.info(f"临期过滤后记录数: {queryset.count()}")

    # 过期天数过滤
    if expired_days and expired_days.isdigit():
        expiration_date = today - timedelta(days=int(expired_days))
        queryset = queryset.filter(
            expected_date__isnull=False,
            expected_date__lt=today,
            expected_date__gte=expiration_date
        )
        logger.info(f"过期过滤后记录数: {queryset.count()}")

    # 最终记录数
    final_count = queryset.count()
    logger.info(f"最终导出记录数: {final_count}")

    # 如果没有记录，返回空响应
    if final_count == 0:
        return HttpResponse("没有找到匹配的记录", status=404)

    # 手动构建数据列表
    data_list = []
    status_display_map = {
        'pending': '待处理',
        'processing': '处理中',
        'resolved': '已解决'
    }

    # 批量处理提高性能
    for record in queryset:
        data_list.append({
            '日期': record.date,
            '时间': record.time.strftime('%H:%M:%S') if record.time else '',
            '车号': record.train_number,
            '故障来源': record.source,
            '故障类型': record.fault_type,
            '故障现象': record.phenomenon,
            '位置': record.location,
            '状态': status_display_map.get(record.status, record.status),
            '跟进技术人员': record.technician,
            '故障系统': record.system.name if record.system else '',
            '二级分类': record.secondary.name if record.secondary else '',
            '三级分类': record.third.name if record.third else '',
            '四级分类': record.fourth.name if record.fourth else '',
            '故障原因': record.cause,
            '报告人': record.reporter,
            '受理人': record.receiver,
            '当前进度': record.progress,
            '预计处理日期': record.expected_date,
            '处理办法': record.solution,
            '是否更换备件': '是' if record.part_replaced else '否',
            '备件名称': record.part_name,
            '备件数量': record.part_quantity,
            '辅料': record.materials,
            '工具': record.tools,
            '故障定位用时(分钟)': record.location_time,
            '更换用时(分钟)': record.replacement_time,
            '遗留项处理日期': record.legacy_date,
            '登记人': record.registrar,
            '登记时间': record.registration_time.strftime('%Y-%m-%d %H:%M:%S'),
            '是否有效': '是' if record.is_valid else '否',
            '图片数量': record.image_count,
            '图片路径': ', '.join(record.image_paths) if record.image_paths else '',
            '修改人': record.modified_by,
            '修改时间': record.modified_at.strftime('%Y-%m-%d %H:%M:%S') if record.modified_at else ''
        })

    # 创建DataFrame
    df = pd.DataFrame(data_list)

    # 创建Excel响应
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    filename = f"故障记录_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # 使用Pandas写入Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='故障记录')

    return response


@require_http_methods(['GET', 'POST'])
def add_fault_data(request):
    if request.method == 'GET':
        return render(request, 'addFaultData.html')
    else:
        try:
            # 状态映射
            STATUS_MAP = {
                '待处理': 'pending',
                '处理中': 'processing',
                '已解决': 'resolved'
            }

            # 处理日期字段
            from django.utils.dateparse import parse_date, parse_time

            try:
                date = parse_date(request.POST.get('日期'))
                time = parse_time(request.POST.get('时间'))
                expected_date = parse_date(request.POST.get('预计处理日期')) if request.POST.get(
                    '预计处理日期') else None
                legacy_date = parse_date(request.POST.get('遗留项处理日期')) if request.POST.get(
                    '遗留项处理日期') else None
            except (ValueError, TypeError) as e:
                return JsonResponse({
                    'success': False,
                    'message': f'日期格式错误: {str(e)}'
                }, status=400)

            # 从表单数据中提取字段
            data = {
                'date': date,
                'time': time,
                'train_number': request.POST.get('车号'),
                'source': request.POST.get('问题来源'),
                'fault_type': request.POST.get('故障类别'),
                'phenomenon': request.POST.get('故障现象'),
                'location': request.POST.get('故障具体位置'),
                'status': STATUS_MAP.get(request.POST.get('状态'), 'pending'),  # 使用状态映射
                'technician': request.POST.get('跟进技术人员'),
                'cause': request.POST.get('故障原因'),
                'reporter': request.POST.get('reporter'),
                'receiver': request.POST.get('受理人'),
                'progress': request.POST.get('当前进度'),
                'expected_date': expected_date,
                'solution': request.POST.get('处理办法'),
                'part_replaced': request.POST.get('是否更换备件') == '是',
                'part_name': request.POST.get('更换备件名称') or None,
                'part_quantity': int(request.POST.get('更换数量')) if request.POST.get('更换数量') else None,
                'materials': request.POST.get('辅料') or None,
                'tools': request.POST.get('工具') or None,
                'location_time': int(request.POST.get('故障定位用时(分钟)')) if request.POST.get(
                    '故障定位用时(分钟)') else None,
                'replacement_time': int(request.POST.get('更换用时(分钟)')) if request.POST.get(
                    '更换用时(分钟)') else None,
                'legacy_date': legacy_date,
                'registrar': request.POST.get('登记人'),
                'is_valid': request.POST.get('是否有效') == '是',
            }

            # 处理外键字段 - 转换为整数ID
            foreign_key_fields = {
                'system_id': request.POST.get('故障系统'),
                'secondary_id': request.POST.get('故障二级分类'),
                'third_id': request.POST.get('三级分类'),
                'fourth_id': request.POST.get('四级分类'),
            }

            for field, value in foreign_key_fields.items():
                if value and value.isdigit():
                    data[field] = int(value)
                else:
                    data[field] = None  # 允许空值

            # 处理图片上传
            image_paths = []
            image_count = int(request.POST.get('imageCount', 0))

            # 创建图片存储目录
            upload_dir = os.path.join(settings.MEDIA_ROOT, 'fault_images')
            if not os.path.exists(upload_dir):
                os.makedirs(upload_dir)

            for i in range(1, image_count + 1):
                image_key = f'image_{i}'
                if image_key in request.FILES:
                    image = request.FILES[image_key]
                    # 生成唯一文件名
                    file_ext = os.path.splitext(image.name)[1]
                    filename = f"{uuid.uuid4().hex}{file_ext}"
                    filepath = os.path.join(upload_dir, filename)

                    # 保存文件
                    with open(filepath, 'wb') as f:
                        for chunk in image.chunks():
                            f.write(chunk)
                    # 存储相对路径
                    relative_path = os.path.join('fault_images', filename)
                    image_paths.append(relative_path)
            # 添加图片相关字段
            data['image_count'] = image_count
            data['image_paths'] = image_paths

            # 记录处理后的数据
            logger.info(f"Creating fault record with data: {data}")

            # 创建故障记录
            fault = FaultRecord.objects.create(**data)

            logger.info(f"Fault record created: ID={fault.id}")

            return JsonResponse({
                'success': True,
                'fault_id': fault.id,
                'accepter': data['receiver']
            })

        except Exception as e:
            logger.error(f"Error creating fault record: {str(e)}", exc_info=True)
            return JsonResponse({
                'success': False,
                'message': str(e)
            }, status=400)


# 图片下载视图
@require_GET
def download_image(request):
    image_path = request.GET.get('path', '')
    if not image_path:
        return HttpResponse("缺少图片路径", status=400)

    # 构建完整路径
    full_path = os.path.join(settings.MEDIA_ROOT, image_path)

    if not os.path.exists(full_path):
        return HttpResponse("图片不存在", status=404)

    # 获取文件名用于下载
    filename = os.path.basename(image_path)

    response = FileResponse(open(full_path, 'rb'))
    response['Content-Disposition'] = f'attachment; filename="{escape_uri_path(filename)}"'
    return response


# 删除用法
def delete_faults(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            ids = data.get('ids', [])

            if not ids:
                return JsonResponse({
                    'success': False,
                    'message': '未提供要删除的ID'
                })

            # 获取要删除的记录
            records_to_delete = FaultRecord.objects.filter(id__in=ids)
            deleted_count = records_to_delete.count()

            # 执行删除
            records_to_delete.delete()

            return JsonResponse({
                'success': True,
                'deleted_count': deleted_count,
                'message': f'成功删除 {deleted_count} 条记录'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'删除失败: {str(e)}'
            })

    return JsonResponse({
        'success': False,
        'message': '无效的请求方法'
    })


@require_GET
def accepter_list(request):
    """获取所有level为1或2的用户列表"""
    accepters = CustomUser.objects.filter(level__in=[1, 2]).values('username')
    return JsonResponse(list(accepters), safe=False)


@require_http_methods(['GET'])
def get_fault_record(request):
    record_id = request.GET.get('id')

    if not record_id:
        return JsonResponse({
            'success': False,
            'message': '缺少记录ID'
        })

    try:
        record = FaultRecord.objects.get(id=record_id)

        # 获取分类名称
        system_name = record.system.name if record.system else ''
        secondary_name = record.secondary.name if record.secondary else ''
        third_name = record.third.name if record.third else ''
        fourth_name = record.fourth.name if record.fourth else ''

        # 准备返回的数据
        record_data = {
            'id': record.id,
            'date': record.date.isoformat() if record.date else None,
            'time': record.time.strftime('%H:%M') if record.time else None,
            'train_number': record.train_number,
            'source': record.source,
            'fault_type': record.fault_type,
            'phenomenon': record.phenomenon,
            'location': record.location,
            'status': record.status,
            'technician': record.technician,
            'system_name': system_name,
            'secondary_name': secondary_name,
            'third_name': third_name,
            'fourth_name': fourth_name,
            'cause': record.cause,
            'reporter': record.reporter,
            'receiver': record.receiver,
            'progress': record.progress,
            'expected_date': record.expected_date.isoformat() if record.expected_date else None,
            'solution': record.solution,
            'part_replaced': record.part_replaced,
            'part_name': record.part_name,
            'part_quantity': record.part_quantity,
            'materials': record.materials,
            'tools': record.tools,
            'location_time': record.location_time,
            'replacement_time': record.replacement_time,
            'legacy_date': record.legacy_date.isoformat() if record.legacy_date else None,
            'registrar': record.registrar,
            'registration_time': record.registration_time.isoformat(),
            'is_valid': record.is_valid,
            'image_count': record.image_count,
            'image_paths': record.image_paths,
            'modified_by': record.modified_by,
            'modified_at': record.modified_at.isoformat() if record.modified_at else None
        }

        return JsonResponse({
            'success': True,
            'record': record_data
        })

    except FaultRecord.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': '记录不存在'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'获取记录失败: {str(e)}'
        })


@require_http_methods(['POST'])
def update_fault_record(request):
    try:
        data = json.loads(request.body)
        record_id = data.get('recordId')

        if not record_id:
            return JsonResponse({
                'success': False,
                'message': '缺少记录ID'
            })

        try:
            record = FaultRecord.objects.get(id=record_id)
        except FaultRecord.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': '记录不存在'
            })

        # 状态映射
        STATUS_MAP = {
            '待处理': 'pending',
            '处理中': 'processing',
            '已解决': 'resolved'
        }

        # 更新记录字段
        record.date = data.get('日期')
        record.time = data.get('时间')
        record.train_number = data.get('车号')
        record.source = data.get('问题来源')
        record.fault_type = data.get('故障类别')
        record.phenomenon = data.get('故障现象')
        record.location = data.get('故障具体位置')
        record.status = STATUS_MAP.get(data.get('状态'), 'pending')
        record.technician = data.get('跟进技术人员')

        # 更新分类字段
        system_id = data.get('故障系统')
        if system_id and system_id.isdigit():
            record.system_id = int(system_id)

        secondary_id = data.get('故障二级分类')
        if secondary_id and secondary_id.isdigit():
            record.secondary_id = int(secondary_id)

        third_id = data.get('三级分类')
        if third_id and third_id.isdigit():
            record.third_id = int(third_id)

        fourth_id = data.get('四级分类')
        if fourth_id and fourth_id.isdigit():
            record.fourth_id = int(fourth_id)

        # 更新其他字段
        record.cause = data.get('故障原因')
        record.reporter = data.get('报告人')
        record.receiver = data.get('受理人')
        record.progress = data.get('当前进度')

        expected_date = data.get('预计处理日期')
        record.expected_date = expected_date if expected_date else None

        record.solution = data.get('处理办法')

        # 备件信息
        part_replaced = data.get('是否更换备件')
        record.part_replaced = (part_replaced == '是')
        record.part_name = data.get('更换备件名称') if record.part_replaced else None
        record.part_quantity = int(data.get('更换数量')) if record.part_replaced and data.get('更换数量') else None
        record.materials = data.get('辅料') if record.part_replaced else None
        record.tools = data.get('工具') if record.part_replaced else None

        # 用时信息
        record.location_time = int(data.get('故障定位用时(分钟)')) if data.get('故障定位用时(分钟)') else None
        record.replacement_time = int(data.get('更换用时(分钟)')) if data.get('更换用时(分钟)') else None

        legacy_date = data.get('遗留项处理日期')
        record.legacy_date = legacy_date if legacy_date else None

        # 登记信息 - 移除时区转换
        record.registrar = data.get('登记人')
        registration_time = data.get('登记时间')
        if registration_time:
            record.registration_time = datetime.strptime(registration_time, '%Y-%m-%dT%H:%M')

        record.is_valid = (data.get('是否有效') == '是')

        # 修改信息 - 移除时区转换
        record.modified_by = data.get('修改人')
        modified_time = data.get('修改时间')
        if modified_time:
            record.modified_at = datetime.strptime(modified_time, '%Y-%m-%dT%H:%M')
        else:
            record.modified_at = datetime.now()

        record.save()

        return JsonResponse({
            'success': True,
            'message': '记录更新成功'
        })

    except Exception as e:
        logger.error(f"更新记录失败: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': f'更新失败: {str(e)}'
        })


@csrf_exempt
@require_POST
def notify_accepted(request):
    """通知受理人（实际项目中应实现通知逻辑）"""
    accepter = request.POST.get('accepter')
    fault_id = request.POST.get('fault_id')
    message = request.POST.get('message')

    # 实际项目中应实现真正的通知逻辑（邮件、消息系统等）
    print(f"通知受理人 {accepter}: {message}")

    return JsonResponse({'success': True})


def vehicle_list(request):
    try:
        # 查询所有车号
        vehicles = Vehicle.objects.values_list('plate_number', flat=True)
        # 转换为列表并返回JSON
        return JsonResponse(list(vehicles), safe=False)
    except Exception as e:
        # 打印错误信息（在终端可见）
        print(f"Error fetching vehicles: {e}")
        # 返回友好的错误响应
        return JsonResponse({'error': '获取车号列表失败'}, status=500)


def get_systems(request):
    """获取所有系统和车号"""
    systems = System.objects.all().values('id', 'name')
    vehicles = Vehicle.objects.all().values('id', 'plate_number')

    return JsonResponse({
        'systems': list(systems),
        'vehicles': list(vehicles)
    })


def get_all_categories(request):
    """获取所有分类数据"""
    secondaries = SecondaryCategory.objects.all().values('id', 'name', 'system_id')
    thirds = ThirdCategory.objects.all().values('id', 'name', 'secondary_id')
    fourths = FourthCategory.objects.all().values('id', 'name', 'third_id')

    return JsonResponse({
        'secondaries': list(secondaries),
        'thirds': list(thirds),
        'fourths': list(fourths)
    })


@require_GET
def accepter_list(request):
    """获取所有level为1或2的用户列表"""
    accepters = CustomUser.objects.filter(level__in=[1, 2]).values('username')
    return JsonResponse(list(accepters), safe=False)
