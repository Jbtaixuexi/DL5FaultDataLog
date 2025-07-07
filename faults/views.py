from django.core.paginator import Paginator
from django.forms import model_to_dict
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from accounts.models import CustomUser
from .models import FaultRecord, Vehicle, System, SecondaryCategory, ThirdCategory, FourthCategory
import json
from datetime import datetime, timedelta
from django.db.models import Q
from django.shortcuts import render
from django.views.decorators.http import require_http_methods, require_GET, require_POST
import logging

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


@require_GET
def accepter_list(request):
    """获取所有level为1或2的用户列表"""
    accepters = CustomUser.objects.filter(level__in=[1, 2]).values('username')
    return JsonResponse(list(accepters), safe=False)


# 新增用法
@csrf_exempt
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

            for i in range(1, image_count + 1):
                image_key = f'image_{i}'
                if image_key in request.FILES:
                    image = request.FILES[image_key]
                    # 实际项目中应保存文件并获取路径
                    # 这里简化为保存文件名
                    image_paths.append(image.name)

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

# 删除用法
@csrf_exempt
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