from django.core.management.base import BaseCommand
import pandas as pd
from django.db import transaction
from faults.models import FaultRecord, System, SecondaryCategory, ThirdCategory, FourthCategory
import math
import numpy as np


class Command(BaseCommand):
    help = '从Excel导入故障数据'

    def handle(self, *args, **options):
        file_path = r'F:\work\软件\pythonProject\src\data\大连地铁5号线车辆故障信息表.xlsx'

        df = pd.read_excel(
            file_path,
            sheet_name='Sheet1',
            skiprows=0,
            dtype={'车号': str}
        )

        print("Excel文件列名：", df.columns.tolist())
        print("样例数据：\n", df.head(2).to_string())

        df = df.dropna(how='all', axis=1)
        df.columns = df.columns.str.strip()

        def preprocess_row(row):
            """处理特殊字段和空值"""
            # 日期字段转换
            for date_field in ['日期', '预计处理日期', '遗留项处理日期', '登记时间']:
                if pd.notna(row.get(date_field)):
                    try:
                        row[date_field] = pd.to_datetime(row[date_field]).date()
                    except:
                        row[date_field] = None
                else:
                    row[date_field] = None

            # 时间字段
            if pd.notna(row.get('时间')):
                try:
                    row['时间'] = pd.to_datetime(row['时间']).time()
                except:
                    row['时间'] = None
            else:
                row['时间'] = None

            # 布尔字段
            row['是否更换备件'] = row.get('是否更换备件', '') == '是'
            row['是否有效'] = row.get('是否有效', '') == '是'

            # 处理数字字段中的NaN - 更健壮的方法
            for num_field in ['更换数量', '故障定位用时(分钟)', '更换用时(分钟)']:
                value = row.get(num_field)
                if pd.isna(value) or value is None or value == '':
                    row[num_field] = None
                elif isinstance(value, (int, float)):
                    # 检查是否是NaN或无穷大
                    if math.isnan(value) or math.isinf(value):
                        row[num_field] = None
                    else:
                        try:
                            row[num_field] = int(value)
                        except:
                            row[num_field] = None
                else:
                    # 尝试转换字符串为数字
                    try:
                        row[num_field] = int(float(value))
                    except:
                        row[num_field] = None

            return row

        # 应用预处理
        df = df.apply(preprocess_row, axis=1)

        # 确保所有数值字段的NaN被替换为None
        for col in ['更换数量', '故障定位用时(分钟)', '更换用时(分钟)']:
            if col in df.columns:
                df[col] = df[col].replace([np.nan], [None])

        # 打印预处理后的数据以验证
        print("\n预处理后的样例数据：")
        print(df[['更换数量', '故障定位用时(分钟)', '更换用时(分钟)']].head(5))

        # 创建分类映射字典
        system_map = {}
        secondary_map = {}
        third_map = {}
        fourth_map = {}

        # 先处理所有分类，避免重复查询数据库
        for index, row in df.iterrows():
            # 处理系统（一级分类）
            system_name = str(row['故障系统']).strip() if pd.notna(row.get('故障系统')) else None
            if system_name and system_name not in system_map:
                system_obj, created = System.objects.get_or_create(name=system_name)
                system_map[system_name] = system_obj

            # 处理二级分类
            secondary_name = str(row['故障二级分类']).strip() if pd.notna(row.get('故障二级分类')) else None
            if secondary_name and system_name:
                key = f"{system_name}_{secondary_name}"
                if key not in secondary_map:
                    system_obj = system_map.get(system_name)
                    if system_obj:
                        secondary_obj, created = SecondaryCategory.objects.get_or_create(
                            system=system_obj,
                            name=secondary_name
                        )
                        secondary_map[key] = secondary_obj

            # 处理三级分类
            third_name = str(row['三级分类']).strip() if pd.notna(row.get('三级分类')) else None
            if third_name and secondary_name:
                key = f"{system_name}_{secondary_name}_{third_name}"
                if key not in third_map:
                    secondary_key = f"{system_name}_{secondary_name}"
                    secondary_obj = secondary_map.get(secondary_key)
                    if secondary_obj:
                        third_obj, created = ThirdCategory.objects.get_or_create(
                            secondary=secondary_obj,
                            name=third_name
                        )
                        third_map[key] = third_obj

            # 处理四级分类
            fourth_name = str(row['四级分类']).strip() if pd.notna(row.get('四级分类')) else None
            if fourth_name and third_name:
                key = f"{system_name}_{secondary_name}_{third_name}_{fourth_name}"
                if key not in fourth_map:
                    third_key = f"{system_name}_{secondary_name}_{third_name}"
                    third_obj = third_map.get(third_key)
                    if third_obj:
                        fourth_obj, created = FourthCategory.objects.get_or_create(
                            third=third_obj,
                            name=fourth_name
                        )
                        fourth_map[key] = fourth_obj

        with transaction.atomic():
            # 创建故障记录
            fault_records = []
            for index, row in df.iterrows():
                # 获取分类对象
                system_name = str(row['故障系统']).strip() if pd.notna(row.get('故障系统')) else None
                secondary_name = str(row['故障二级分类']).strip() if pd.notna(row.get('故障二级分类')) else None
                third_name = str(row['三级分类']).strip() if pd.notna(row.get('三级分类')) else None
                fourth_name = str(row['四级分类']).strip() if pd.notna(row.get('四级分类')) else None

                system_obj = system_map.get(system_name) if system_name else None

                secondary_obj = None
                if system_name and secondary_name:
                    key = f"{system_name}_{secondary_name}"
                    secondary_obj = secondary_map.get(key)

                third_obj = None
                if system_name and secondary_name and third_name:
                    key = f"{system_name}_{secondary_name}_{third_name}"
                    third_obj = third_map.get(key)

                fourth_obj = None
                if system_name and secondary_name and third_name and fourth_name:
                    key = f"{system_name}_{secondary_name}_{third_name}_{fourth_name}"
                    fourth_obj = fourth_map.get(key)

                # 创建记录前确保所有数值字段为None或整数
                part_quantity = row.get('更换数量')
                if pd.isna(part_quantity) or part_quantity is None:
                    part_quantity = None
                elif isinstance(part_quantity, (int, float)):
                    if math.isnan(part_quantity) or math.isinf(part_quantity):
                        part_quantity = None
                    else:
                        try:
                            part_quantity = int(part_quantity)
                        except:
                            part_quantity = None
                else:
                    part_quantity = None

                # 对其他数值字段做相同处理...
                location_time = row.get('故障定位用时(分钟)')
                if pd.isna(location_time) or location_time is None:
                    location_time = None
                elif isinstance(location_time, (int, float)):
                    if math.isnan(location_time) or math.isinf(location_time):
                        location_time = None
                    else:
                        try:
                            location_time = int(location_time)
                        except:
                            location_time = None
                else:
                    location_time = None

                replacement_time = row.get('更换用时(分钟)')
                if pd.isna(replacement_time) or replacement_time is None:
                    replacement_time = None
                elif isinstance(replacement_time, (int, float)):
                    if math.isnan(replacement_time) or math.isinf(replacement_time):
                        replacement_time = None
                    else:
                        try:
                            replacement_time = int(replacement_time)
                        except:
                            replacement_time = None
                else:
                    replacement_time = None

                record = FaultRecord(
                    date=row['日期'] if pd.notna(row.get('日期')) else None,
                    time=row['时间'] if pd.notna(row.get('时间')) else None,
                    train_number=str(row['车号']) if pd.notna(row.get('车号')) else "",
                    source=str(row['问题来源']) if pd.notna(row.get('问题来源')) else "",
                    fault_type=str(row['故障类别']) if pd.notna(row.get('故障类别')) else "",
                    phenomenon=str(row['故障现象']) if pd.notna(row.get('故障现象')) else "",
                    location=str(row['故障具体位置']) if pd.notna(row.get('故障具体位置')) else "",
                    status='pending',
                    technician=str(row.get('跟进技术人员', '')) if pd.notna(row.get('跟进技术人员')) else "",
                    # 使用分类对象而不是字符串
                    system=system_obj,
                    secondary=secondary_obj,
                    third=third_obj,
                    fourth=fourth_obj,
                    cause=str(row.get('故障原因', '')) if pd.notna(row.get('故障原因')) else "",
                    reporter=str(row.get('报告人', '')) if pd.notna(row.get('报告人')) else "",
                    receiver=str(row.get('受理人', '')) if pd.notna(row.get('受理人')) else "",
                    progress=str(row.get('当前进度', '')) if pd.notna(row.get('当前进度')) else "",
                    expected_date=row.get('预计处理日期'),
                    solution=str(row.get('处理办法', '')) if pd.notna(row.get('处理办法')) else "",
                    part_replaced=row.get('是否更换备件', False),
                    part_name=str(row.get('更换备件名称', '')) if pd.notna(row.get('更换备件名称')) else "",
                    part_quantity=part_quantity,  # 已经处理过的值
                    materials=str(row.get('辅料', '')) if pd.notna(row.get('辅料')) else "",
                    tools=str(row.get('工具', '')) if pd.notna(row.get('工具')) else "",
                    location_time=location_time,  # 已经处理过的值
                    replacement_time=replacement_time,  # 已经处理过的值
                    legacy_date=row.get('遗留项处理日期'),
                    registrar=str(row.get('登记人', '')) if pd.notna(row.get('登记人')) else "",
                    is_valid=row.get('是否有效', True)
                )
                fault_records.append(record)

                # 打印调试信息
                if index < 5:  # 只打印前5行调试信息
                    print(
                        f"行 {index}: system = {system_obj}, secondary = {secondary_obj}, third = {third_obj}, fourth = {fourth_obj}")

            # 批量创建故障记录
            self.stdout.write(self.style.SUCCESS(f"准备创建 {len(fault_records)} 条故障记录"))
            FaultRecord.objects.bulk_create(fault_records)
            self.stdout.write(self.style.SUCCESS("故障记录导入成功!"))
