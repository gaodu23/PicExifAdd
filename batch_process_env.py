import os
import glob
from batch_add_gps_info import process_images_from_csv

# 可选：相机参数文件路径（如有需要可填写）
opt_file = r'e:\FLY\PicExifAdd\cameraInfo\4200-40.opt'

def find_csv_and_jpg(folder):
    csv_files = glob.glob(os.path.join(folder, '*.csv'))
    jpg_files = glob.glob(os.path.join(folder, '*.jpg')) + glob.glob(os.path.join(folder, '*.jpeg'))
    return csv_files, jpg_files


def run_all_tasks():
    # 输入输出路径配对
    task_pairs = [
        (r'Z:\202509宁晋环境\0907\21', r'Z:\yolo\XY-YOLO-Tools\train_data\0907\images'),
        (r'Z:\202509宁晋环境\0907\22', r'Z:\yolo\XY-YOLO-Tools\train_data\0907\images'),
        (r'Z:\202509宁晋环境\0907\23', r'Z:\yolo\XY-YOLO-Tools\train_data\0907\images'),
        (r'Z:\202509宁晋环境\0907\24', r'Z:\yolo\XY-YOLO-Tools\train_data\0907\images'),
        (r'Z:\202509宁晋环境\0907\31', r'Z:\yolo\XY-YOLO-Tools\train_data\0907\images'),
        (r'Z:\202509宁晋环境\0907\32', r'Z:\yolo\XY-YOLO-Tools\train_data\0907\images'),
        (r'Z:\202509宁晋环境\0907\33', r'Z:\yolo\XY-YOLO-Tools\train_data\0907\images'),
    ]
    for idx, (folder, out_folder) in enumerate(task_pairs, 1):
        print(f"\n{'='*60}")
        print(f"任务{idx}: 目录: {folder}")
        csv_files, jpg_files = find_csv_and_jpg(folder)
        print(f"  找到CSV文件: {csv_files}")
        print(f"  找到JPG文件数量: {len(jpg_files)}")
        if not csv_files:
            print("  未找到CSV文件，跳过！")
            print(f"{'='*60}\n")
            continue
        if len(csv_files) > 1:
            print("  发现多个CSV文件，请手动处理，跳过！")
            print(f"{'='*60}\n")
            continue
        # 统计CSV行数和文件名
        import pandas as pd
        try:
            df = pd.read_csv(csv_files[0], header=None, encoding='utf-8-sig')
            csv_count = len(df)
            # 取csv文件名列（假定在第4列/索引3）
            csv_names = set(str(row[3]).strip() for _, row in df.iterrows())
        except Exception as e:
            print(f"  CSV读取失败: {e}，跳过！")
            print(f"{'='*60}\n")
            continue
        print(f"  CSV记录数: {csv_count}")
        # 取照片文件名（不含路径）
        jpg_names = set(os.path.basename(f) for f in jpg_files)
        if csv_count != len(jpg_files):
            print(f"  CSV记录数与JPG文件数不一致，跳过！")
            print(f"  CSV文件名: {sorted(csv_names)}")
            print(f"  照片文件名: {sorted(jpg_names)}")
            print(f"{'='*60}\n")
            continue
        # 文件名一一对应校验
        if csv_names != jpg_names:
            print(f"  CSV与照片文件名不完全对应，跳过！")
            print(f"  CSV文件名: {sorted(csv_names)}")
            print(f"  照片文件名: {sorted(jpg_names)}")
            print(f"{'='*60}\n")
            continue
        print(f"  输出文件夹: {out_folder}")
        print(f"{'-'*60}")
        result = process_images_from_csv(csv_files[0], folder, opt_file=opt_file, output_dir=out_folder)
        print(f"结果: 成功={result['success']} 失败={result['failed']} 跳过={result['skipped']}\n")
        if result['errors']:
            print("错误信息:")
            for err in result['errors']:
                print(f"  - {err}")
        print(f"{'='*60}\n")

if __name__ == "__main__":
    run_all_tasks()
