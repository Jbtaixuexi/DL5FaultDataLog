import pandas as pd
from io import StringIO
from django.db import transaction
from faults.models import ComponentCategory, FaultRecord

# 1. 准备数据（直接使用您提供的文本内容）
file_path = r'F:\work\软件\pythonProject\src\data\大连地铁5号线车辆故障信息表.xlsx'

# 2. 使用Pandas解析表格
df = pd.read_excel(
    file_path,
    sheet_name='Sheet1',  # 指定工作表
    skiprows=1,           # 跳过首行（如果有标题说明）
    dtype={'车号': str}    # 强制车号为字符串类型
)

# 清理列名和空值
df = df.dropna(how='all', axis=1)  # 删除空列
df.columns = df.columns.str.strip()


# 3. 预处理数据
def preprocess_row(row):
    """处理特殊字段和空值"""
    # 日期字段转换
    for date_field in ['日期', '预计处理日期', '遗留项处理日期', '登记时间']:
        if pd.notna(row.get(date_field)):
            row[date_field] = pd.to_datetime(row[date_field]).date()

    # 时间字段
    if pd.notna(row.get('时间')):
        row['时间'] = pd.to_datetime(row['时间']).time()

    # 布尔字段
    row['是否更换备件'] = row.get('是否更换备件', '') == '是'
    row['是否有效'] = row.get('是否有效', '') == '是'

    return row


df = df.apply(preprocess_row, axis=1)

# 4. 批量创建组件分类（使用字典缓存避免重复查询）
category_cache = {}
with transaction.atomic():
    # 先处理所有ComponentCategory
    categories = []
    for _, row in df.iterrows():
        key = (row['故障系统'], row['故障二级分类'], row['三级分类'], row['四级分类'])
        if key not in category_cache:
            category = ComponentCategory(
                system=row['故障系统'],
                secondary=row['故障二级分类'],
                third=row['三级分类'],
                fourth=row['四级分类']
            )
            categories.append(category)
            category_cache[key] = category

    # 批量创建分类
    ComponentCategory.objects.bulk_create(categories, ignore_conflicts=True)

    # 5. 创建故障记录
    fault_records = []
    for _, row in df.iterrows():
        # 获取对应的分类实例
        key = (row['故障系统'], row['故障二级分类'], row['三级分类'], row['四级分类'])
        category = category_cache[key]

        # 映射到模型字段
        record = FaultRecord(
            date=row['日期'],
            time=row['时间'],
            train_number=row['车号'],
            source=row['问题来源'],
            fault_type=row['故障类别'],
            phenomenon=row['故障现象'],
            location=row['故障具体位置'],
            status='pending',  # 根据实际状态映射
            technician=row.get('跟进技术人员', ''),
            category=category,
            cause=row.get('故障原因', ''),
            reporter=row.get('报告人', ''),
            receiver=row.get('受理人', ''),
            progress=row.get('当前进度', ''),
            expected_date=row.get('预计处理日期'),
            solution=row.get('处理办法', ''),
            part_replaced=row.get('是否更换备件', False),
            part_name=row.get('更换备件名称', ''),
            part_quantity=row.get('更换数量'),
            materials=row.get('辅料', ''),
            tools=row.get('工具', ''),
            location_time=row.get('故障定位用时(分钟)'),
            replacement_time=row.get('更换用时(分钟)'),
            legacy_date=row.get('遗留项处理日期'),
            registrar=row.get('登记人', ''),
            is_valid=row.get('是否有效', True)
        )
        fault_records.append(record)

    # 批量创建记录
    FaultRecord.objects.bulk_create(fault_records)