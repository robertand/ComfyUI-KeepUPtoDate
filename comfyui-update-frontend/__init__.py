import subprocess
import sys
import os
import site
from pathlib import Path

class UpdateComfyUIPackages:
    def __init__(self):
        pass
    
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "run_update": (["yes", "no"], {"default": "yes"}),
                "update_requirements": (["yes", "no"], {"default": "yes"}),
                "update_frontend": (["yes", "no"], {"default": "yes"}),
                "update_templates": (["yes", "no"], {"default": "yes"}),
            }
        }
    
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("status",)
    FUNCTION = "update_packages"
    CATEGORY = "utils"

    def update_packages(self, run_update, update_requirements, update_frontend, update_templates):
        """Rulează actualizările pentru pachetele ComfyUI"""
        
        if run_update == "no":
            return ("Update skipped by user choice.",)
        
        results = []
        results.append("🔄 Starting ComfyUI package updates...")
        results.append("="*50)
        
        # Obține calea către python executabil și rădăcina ComfyUI
        python_exe = sys.executable
        comfyui_root = self.get_comfyui_root()
        results.append(f"📂 ComfyUI root: {comfyui_root}")
        
        # 1. MAI ÎNTÂI: Update requirements.txt from root
        if update_requirements == "yes":
            results.extend(self.update_requirements_file(comfyui_root, python_exe))
        
        # 2. DUPĂ ACEA: Update frontend package
        if update_frontend == "yes":
            results.extend(self.run_pip_install(python_exe, "comfyui-frontend-package"))
        
        # 3. LA SFÂRȘIT: Update templates package
        if update_templates == "yes":
            results.extend(self.run_pip_install(python_exe, "comfyui-workflow-templates"))
        
        results.append("\n" + "="*50)
        results.append("✅ All updates completed!")
        results.append("🔁 Recomandare: Repornește ComfyUI pentru ca modificările să aibă efect!")
        
        return ("\n".join(results),)
    
    def get_comfyui_root(self):
        """Determină calea către rădăcina ComfyUI"""
        # Acest nod se află în: ComfyUI/custom_nodes/comfyui-update-frontend/__init__.py
        current_file = Path(__file__).resolve()  # .../custom_nodes/comfyui-update-frontend/__init__.py
        custom_nodes_dir = current_file.parent.parent  # .../custom_nodes/
        comfyui_root = custom_nodes_dir.parent  # .../ComfyUI/
        return str(comfyui_root)
    
    def run_pip_install(self, python_exe, package_name):
        """Rulează pip install -U pentru un pachet"""
        results = []
        results.append(f"\n📦 Updating {package_name}...")
        
        try:
            process = subprocess.run(
                [python_exe, "-m", "pip", "install", "-U", package_name],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if process.returncode == 0:
                if "Successfully installed" in process.stdout:
                    for line in process.stdout.split('\n'):
                        if "Successfully installed" in line:
                            results.append(f"✅ {line.strip()}")
                            break
                elif "Requirement already satisfied" in process.stdout:
                    # Extrage versiunea existentă
                    for line in process.stdout.split('\n'):
                        if "Requirement already satisfied" in line and package_name in line:
                            results.append(f"✅ {line.strip()}")
                            break
                    else:
                        results.append(f"✅ {package_name} already up to date")
                else:
                    results.append(f"✅ {package_name} processed")
            else:
                results.append(f"❌ Error updating {package_name}")
                if process.stderr:
                    results.append(f"   {process.stderr.strip()}")
                    
        except subprocess.TimeoutExpired:
            results.append(f"❌ Update timed out after 120 seconds")
        except Exception as e:
            results.append(f"❌ Exception: {str(e)}")
        
        return results
    
    def update_requirements_file(self, comfyui_root, python_exe):
        """Rulează pip install -r requirements.txt din rădăcina ComfyUI"""
        results = []
        results.append("\n📋 STEP 1: Updating requirements.txt dependencies...")
        
        requirements_path = os.path.join(comfyui_root, "requirements.txt")
        
        # Verifică dacă requirements.txt există
        if not os.path.exists(requirements_path):
            results.append("❌ requirements.txt not found in ComfyUI root!")
            return results
        
        results.append(f"📄 Found: {requirements_path}")
        
        try:
            # Rulează pip install -r requirements.txt --upgrade
            results.append("⚙️ Running: pip install -r requirements.txt --upgrade")
            
            process = subprocess.run(
                [python_exe, "-m", "pip", "install", "-r", requirements_path, "--upgrade"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute pentru multe dependențe
            )
            
            if process.returncode == 0:
                results.append("✅ Requirements successfully updated!")
                
                # Analizează output-ul pentru a vedea ce s-a actualizat
                output_lines = process.stdout.split('\n')
                
                # Caută pachete instalate/actualizate
                updated_packages = []
                for line in output_lines:
                    if "Successfully installed" in line:
                        packages = line.replace("Successfully installed", "").strip()
                        updated_packages.append(packages)
                
                if updated_packages:
                    results.append(f"   📦 Updated: {', '.join(updated_packages)}")
                else:
                    # Verifică dacă toate erau deja actualizate
                    if "Requirement already satisfied" in process.stdout and "Successfully installed" not in process.stdout:
                        results.append("   ✅ All requirements already up to date")
                
                # Afișează un scurt rezumat (ultimele 5 linii relevante)
                relevant_lines = []
                for line in output_lines:
                    if any(keyword in line for keyword in ["Successfully installed", "Requirement already satisfied", "Collecting", "Installing"]):
                        relevant_lines.append(f"   {line.strip()}")
                
                if relevant_lines:
                    results.append("\n📊 Requirements summary:")
                    results.extend(relevant_lines[-5:])  # Ultimele 5 linii relevante
                    
            else:
                results.append(f"❌ Error updating requirements")
                if process.stderr:
                    results.append(f"   {process.stderr.strip()}")
                    
        except subprocess.TimeoutExpired:
            results.append("❌ Requirements update timed out after 5 minutes")
        except Exception as e:
            results.append(f"❌ Exception: {str(e)}")
        
        return results

# Înregistrează nodul
NODE_CLASS_MAPPINGS = {
    "Update ComfyUI Packages": UpdateComfyUIPackages
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "Update ComfyUI Packages": "🔄 Update ComfyUI (Requirements → Frontend → Templates)"
}

# =============================================
# AUTO-UPDATE LA PORNIRE
# =============================================
print("\n" + "="*70)
print("  🔧 COMFYUI PACKAGE UPDATER - AUTO-UPDATE MODE")
print("="*70)

try:
    python_exe = sys.executable
    comfyui_root = str(Path(__file__).resolve().parent.parent.parent)
    updates_run = []
    
    print(f"  📂 ComfyUI root: {comfyui_root}")
    print("-" * 70)
    
    # STEP 1: Update requirements.txt
    requirements_path = os.path.join(comfyui_root, "requirements.txt")
    if os.path.exists(requirements_path):
        print("  📋 STEP 1: Checking requirements.txt...")
        proc_r = subprocess.run(
            [python_exe, "-m", "pip", "install", "-r", requirements_path, "--upgrade"],
            capture_output=True, text=True, timeout=180
        )
        if proc_r.returncode == 0:
            if "Successfully installed" in proc_r.stdout:
                print("  ✅ Requirements UPDATED:")
                for line in proc_r.stdout.split('\n'):
                    if "Successfully installed" in line:
                        print(f"     {line.strip()}")
                updates_run.append("requirements")
            elif "Requirement already satisfied" in proc_r.stdout and "Successfully installed" not in proc_r.stdout:
                print("  ✅ All requirements already up to date")
            else:
                print("  ✅ Requirements check completed")
        else:
            print("  ⚠️ Requirements check had issues")
    else:
        print("  ⚠️ requirements.txt not found")
    
    # STEP 2: Update frontend package
    print("\n  📦 STEP 2: Checking comfyui-frontend-package...")
    proc_f = subprocess.run(
        [python_exe, "-m", "pip", "install", "-U", "comfyui-frontend-package"],
        capture_output=True, text=True, timeout=60
    )
    if proc_f.returncode == 0:
        if "Successfully installed" in proc_f.stdout:
            for line in proc_f.stdout.split('\n'):
                if "Successfully installed" in line:
                    print(f"  ✅ Frontend UPDATED: {line.strip()}")
                    updates_run.append("frontend")
                    break
        elif "Requirement already satisfied" in proc_f.stdout:
            print("  ✅ Frontend already up to date")
        else:
            print("  ✅ Frontend check completed")
    
    # STEP 3: Update templates package
    print("\n  📦 STEP 3: Checking comfyui-workflow-templates...")
    proc_t = subprocess.run(
        [python_exe, "-m", "pip", "install", "-U", "comfyui-workflow-templates"],
        capture_output=True, text=True, timeout=60
    )
    if proc_t.returncode == 0:
        if "Successfully installed" in proc_t.stdout:
            for line in proc_t.stdout.split('\n'):
                if "Successfully installed" in line:
                    print(f"  ✅ Templates UPDATED: {line.strip()}")
                    updates_run.append("templates")
                    break
        elif "Requirement already satisfied" in proc_t.stdout:
            print("  ✅ Templates already up to date")
        else:
            print("  ✅ Templates check completed")
    
    # Rezumat final
    print("\n" + "-" * 70)
    if updates_run:
        print("  📊 UPDATES INSTALLED (in order):")
        for i, update in enumerate(updates_run, 1):
            print(f"     {i}. {update}")
    else:
        print("  📊 All packages were already up to date")
    print("="*70 + "\n")
    
except Exception as e:
    print(f"  ❌ Auto-update error: {str(e)}")
    print("="*70 + "\n")

print("📝 Pentru update manual, folosește nodul '🔄 Update ComfyUI' în workflow")
print("   din categoria 'utils'")
print("-" * 70 + "\n")