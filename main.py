from fastapi import FastAPI, UploadFile, File, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from contextlib import asynccontextmanager
import os
import shutil
import zipfile
import tempfile
from pathlib import Path
import subprocess
import json
import threading
import time
from datetime import datetime, timedelta

# 清理配置
TEMP_TTL_HOURS = 1  # temp文件夹TTL：1小时
OUTPUT_TTL_HOURS = 24  # output文件夹TTL：24小时
CLEANUP_INTERVAL_MINUTES = 10  # 清理线程执行间隔：10分钟

# 清理线程控制
cleanup_thread_running = False
cleanup_thread = None


def cleanup_old_files():
    """
    清理过期的临时文件和输出文件
    temp文件夹：TTL 1小时
    output文件夹：TTL 24小时
    """
    current_time = time.time()
    temp_ttl_seconds = TEMP_TTL_HOURS * 3600
    output_ttl_seconds = OUTPUT_TTL_HOURS * 3600
    
    cleaned_temp = 0
    cleaned_output = 0
    
    try:
        # 清理temp文件夹
        if TEMP_DIR.exists():
            for item in TEMP_DIR.iterdir():
                if item.is_dir():
                    try:
                        # 获取文件夹的修改时间
                        mtime = item.stat().st_mtime
                        age_seconds = current_time - mtime
                        
                        if age_seconds > temp_ttl_seconds:
                            # 删除过期的temp文件夹
                            shutil.rmtree(item, ignore_errors=True)
                            cleaned_temp += 1
                            print(f"[清理] 删除过期的temp文件夹: {item.name} (年龄: {age_seconds/3600:.2f}小时)")
                    except (OSError, PermissionError) as e:
                        print(f"[清理] 无法删除temp文件夹 {item.name}: {e}")
        
        # 清理output文件夹
        if OUTPUT_DIR.exists():
            for item in OUTPUT_DIR.iterdir():
                if item.is_dir():
                    try:
                        # 获取文件夹的修改时间
                        mtime = item.stat().st_mtime
                        age_seconds = current_time - mtime
                        
                        if age_seconds > output_ttl_seconds:
                            # 删除过期的output文件夹
                            shutil.rmtree(item, ignore_errors=True)
                            cleaned_output += 1
                            print(f"[清理] 删除过期的output文件夹: {item.name} (年龄: {age_seconds/3600:.2f}小时)")
                    except (OSError, PermissionError) as e:
                        print(f"[清理] 无法删除output文件夹 {item.name}: {e}")
        
        if cleaned_temp > 0 or cleaned_output > 0:
            print(f"[清理] 清理完成: temp={cleaned_temp}个, output={cleaned_output}个")
    
    except Exception as e:
        print(f"[清理] 清理过程出错: {e}")


def cleanup_worker():
    """
    后台清理线程工作函数
    每10分钟执行一次清理
    """
    global cleanup_thread_running
    cleanup_thread_running = True
    
    print(f"[清理] 清理线程已启动，每{CLEANUP_INTERVAL_MINUTES}分钟执行一次清理")
    print(f"[清理] temp文件夹TTL: {TEMP_TTL_HOURS}小时, output文件夹TTL: {OUTPUT_TTL_HOURS}小时")
    
    while cleanup_thread_running:
        try:
            cleanup_old_files()
        except Exception as e:
            print(f"[清理] 清理线程执行出错: {e}")
        
        # 等待指定时间后再次执行
        for _ in range(CLEANUP_INTERVAL_MINUTES * 60):
            if not cleanup_thread_running:
                break
            time.sleep(1)
    
    print("[清理] 清理线程已停止")


def start_cleanup_thread():
    """
    启动清理线程
    """
    global cleanup_thread
    if cleanup_thread is None or not cleanup_thread.is_alive():
        cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        cleanup_thread.start()
        print("[清理] 清理线程启动成功")


def stop_cleanup_thread():
    """
    停止清理线程
    """
    global cleanup_thread_running, cleanup_thread
    cleanup_thread_running = False
    if cleanup_thread and cleanup_thread.is_alive():
        cleanup_thread.join(timeout=5)
        print("[清理] 清理线程已停止")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时启动清理线程，关闭时停止清理线程
    """
    # 启动时执行
    start_cleanup_thread()
    # 启动时立即执行一次清理
    cleanup_old_files()
    yield
    # 关闭时执行
    stop_cleanup_thread()


app = FastAPI(title="DITA文件验证平台", lifespan=lifespan)

# 配置CORS，允许前端访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件服务（用于前端）
app.mount("/static", StaticFiles(directory="static"), name="static")

# 临时文件目录
TEMP_DIR = Path("temp")
TEMP_DIR.mkdir(exist_ok=True)

# 输出目录
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


class ValidateRequest(BaseModel):
    temp_id: str


def is_empty_folder(folder_path: Path) -> bool:
    """
    检查文件夹是否为空（忽略空子文件夹）
    """
    try:
        # 检查是否有任何文件（不包括空文件夹）
        for item in folder_path.iterdir():
            if item.is_file():
                return False
            elif item.is_dir():
                # 递归检查子目录是否有文件
                if not is_empty_folder(item):
                    return False
        return True
    except (PermissionError, OSError):
        return True


def find_dita_root_folder(extract_folder: Path) -> tuple[Path | None, Path | None]:
    """
    查找DITA根文件夹
    返回: (根文件夹路径, infotree.xml文件路径)
    支持结构：
    - 根目录下有.dita文件
    - out/子目录下有infotree.xml文件
    处理浏览器解压可能产生的空文件夹
    """
    # 首先查找包含.dita文件的目录
    dita_root = None
    for root, dirs, files in os.walk(extract_folder):
        root_path = Path(root)
        
        # 跳过空文件夹（浏览器解压可能产生的空文件夹）
        if is_empty_folder(root_path):
            continue
        
        # 检查是否有.dita文件（只检查当前目录，不递归）
        dita_files = [f for f in files if f.endswith('.dita')]
        if dita_files:
            dita_root = root_path
            break
    
    if dita_root is None:
        return None, None
    
    # 在根目录或其子目录中查找infotree.xml
    infotree_path = None
    
    # 先检查out/子目录（最常见的情况）
    out_folder = dita_root / "out"
    if out_folder.exists() and (out_folder / "infotree.xml").exists():
        infotree_path = out_folder / "infotree.xml"
    # 检查根目录
    elif (dita_root / "infotree.xml").exists():
        infotree_path = dita_root / "infotree.xml"
    # 递归查找所有子目录（处理其他可能的位置）
    else:
        for root, dirs, files in os.walk(dita_root):
            root_path = Path(root)
            # 跳过空文件夹
            if is_empty_folder(root_path):
                continue
            if "infotree.xml" in files:
                infotree_path = root_path / "infotree.xml"
                break
    
    return dita_root, infotree_path


def validate_dita_structure(folder_path: Path) -> tuple[bool, str]:
    """
    验证DITA文件夹结构是否符合要求
    要求：
    - 根目录包含若干个.dita文件
    - infotree.xml文件可以在根目录或out/子目录中
    """
    if not folder_path.exists():
        return False, "文件夹不存在"
    
    # 检查是否有dita文件（在根目录）
    dita_files = list(folder_path.glob("*.dita"))
    if len(dita_files) == 0:
        return False, "文件夹根目录中没有找到.dita文件"
    
    # 检查是否有infotree.xml文件（可能在根目录或out/子目录）
    infotree_file = folder_path / "infotree.xml"
    infotree_file_out = folder_path / "out" / "infotree.xml"
    
    if not infotree_file.exists() and not infotree_file_out.exists():
        return False, "缺少infotree.xml文件（应在根目录或out/子目录中）"
    
    return True, f"验证通过，找到{len(dita_files)}个DITA文件"


@app.get("/")
async def root():
    """返回前端页面"""
    return FileResponse("static/index.html")


@app.post("/api/upload")
async def upload_dita_folder(file: UploadFile = File(...)):
    """
    上传DITA文件夹（zip格式）
    """
    try:
        # 创建临时目录
        temp_id = os.urandom(8).hex()
        temp_folder = TEMP_DIR / temp_id
        temp_folder.mkdir(exist_ok=True)
        
        # 保存上传的zip文件
        filename = file.filename or "uploaded.zip"
        zip_path = temp_folder / filename
        with open(zip_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        # 解压zip文件
        extract_folder = temp_folder / "extracted"
        extract_folder.mkdir(exist_ok=True)
        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_folder)
        
        # 查找解压后的DITA根文件夹
        # 支持结构：根目录有.dita文件，out/子目录有infotree.xml
        dita_folder, infotree_path = find_dita_root_folder(extract_folder)
        
        if dita_folder is None:
            return JSONResponse(
                status_code=400,
                content={"error": "上传的文件中未找到包含.dita文件的文件夹"}
            )
        
        if infotree_path is None:
            return JSONResponse(
                status_code=400,
                content={"error": "未找到infotree.xml文件（应在根目录或out/子目录中）"}
            )
        
        # 验证文件夹结构
        is_valid, message = validate_dita_structure(dita_folder)
        if not is_valid:
            return JSONResponse(
                status_code=400,
                content={"error": message}
            )
        
        return JSONResponse(content={
            "success": True,
            "message": message,
            "temp_id": temp_id,
            "dita_folder": str(dita_folder)
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"上传失败: {str(e)}"}
        )


@app.post("/api/validate")
async def validate_dita(request: ValidateRequest):
    """
    执行DITA文件验证
    1. 运行dita2json.py，输入是DITA文件夹，输出JSON文件夹和Excel1
    2. 运行e_extract.py，输入是JSON文件夹，输出Excel2
    """
    try:
        temp_id = request.temp_id
        temp_folder = TEMP_DIR / temp_id
        if not temp_folder.exists():
            return JSONResponse(
                status_code=404,
                content={"error": "临时文件夹不存在"}
            )
        
        # 查找DITA根文件夹
        extract_folder = temp_folder / "extracted"
        if not extract_folder.exists():
            return JSONResponse(
                status_code=400,
                content={"error": "解压文件夹不存在"}
            )
        
        dita_folder, infotree_path = find_dita_root_folder(extract_folder)
        
        if dita_folder is None:
            return JSONResponse(
                status_code=400,
                content={"error": "未找到包含.dita文件的文件夹"}
            )
        
        if infotree_path is None:
            return JSONResponse(
                status_code=400,
                content={"error": "未找到infotree.xml文件"}
            )
        
        # 创建输出目录
        output_folder = OUTPUT_DIR / temp_id
        output_folder.mkdir(exist_ok=True)
        
        # 第一步：运行dita2json.py
        json_output_folder = output_folder / "json_output"
        json_output_folder.mkdir(exist_ok=True)
        
        excel1_path = output_folder / "excel1.xlsx"
        
        try:
            # 调用dita2json.py
            result1 = subprocess.run(
                ["python", "dita2json.py", str(dita_folder), str(json_output_folder), str(excel1_path)],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result1.returncode != 0:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"dita2json.py执行失败: {result1.stderr}"}
                )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"执行dita2json.py时出错: {str(e)}"}
            )
        
        # 检查JSON文件夹是否存在
        if not json_output_folder.exists() or not any(json_output_folder.iterdir()):
            return JSONResponse(
                status_code=500,
                content={"error": "dita2json.py未生成JSON文件"}
            )
        
        # 第二步：运行e_extract.py
        excel2_path = output_folder / "excel2.xlsx"
        
        try:
            # 调用e_extract.py
            result2 = subprocess.run(
                ["python", "e_extract.py", str(json_output_folder), str(excel2_path)],
                capture_output=True,
                text=True,
                cwd=os.getcwd()
            )
            
            if result2.returncode != 0:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"e_extract.py执行失败: {result2.stderr}"}
                )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"error": f"执行e_extract.py时出错: {str(e)}"}
            )
        
        # 检查Excel文件是否存在
        if not excel1_path.exists():
            return JSONResponse(
                status_code=500,
                content={"error": "Excel1文件未生成"}
            )
        
        if not excel2_path.exists():
            return JSONResponse(
                status_code=500,
                content={"error": "Excel2文件未生成"}
            )
        
        return JSONResponse(content={
            "success": True,
            "message": "验证完成",
            "excel1": f"/api/download/{temp_id}/excel1.xlsx",
            "excel2": f"/api/download/{temp_id}/excel2.xlsx"
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"验证过程出错: {str(e)}"}
        )


@app.get("/api/download/{temp_id}/{filename}")
async def download_file(temp_id: str, filename: str):
    """
    下载生成的Excel文件
    """
    file_path = OUTPUT_DIR / temp_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

