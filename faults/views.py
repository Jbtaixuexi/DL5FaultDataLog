from django.core.paginator import Paginator
from django.forms import model_to_dict
from django.http import JsonResponse
from .models import FaultRecord
import json
from datetime import datetime, timedelta
from django.db.models import Q
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
import logging

logger = logging.getLogger(__name__)


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


@require_http_methods(['GET','POST'])
def add_fault_data(request):
    if request.method == 'GET':
        return render(request,'addFaultData.html')
    pass
