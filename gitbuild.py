from git import Repo
import json
import os.path
from optparse import OptionParser
from subprocess import call
import sys
import os
chrome_dir_cfg = "chromium_dir";
cef_dir_cfg = "cef_dir";
cef_vidyo_remote_url_cfg = "cef_vidyo_remote_url";
chromium_vidyo_remote_url_cfg = "chrome_vidyo_remote_url";
local_build_number_cfg = "local_build_number";
machine_config_file = "machine.config.json"
global_config_file = "global.config.json"
vidyo_remote_name = "vidyo"
build_output_dir_cfg = "build_output_dir";

config = {};
if sys.platform == 'win32':
  platform = 'windows'
elif sys.platform == 'darwin':
  platform = 'macosx'
elif sys.platform.startswith('linux'):
  platform = 'linux'
else:
  print 'Unknown operating system platform'
  sys.exit()

# Script extension.
if platform == 'windows':
  script_ext = '.bat'
else:
  script_ext = '.sh'
  
#hack
x64build = True;
if x64build and platform != 'windows' and platform != 'macosx':
  print 'The x64 build option is only used on Windows and Mac OS X.'
  sys.exit()

if platform == 'windows' and not 'GYP_MSVS_VERSION' in os.environ.keys():
  print 'You must set the GYP_MSVS_VERSION environment variable on Windows.'
  sys.exit()      
def import_file(full_path_to_module):
    try:
        import os
        module_dir, module_file = os.path.split(full_path_to_module)
        module_name, module_ext = os.path.splitext(module_file)
        save_cwd = os.getcwd()
        os.chdir(module_dir)
        module_obj = __import__(module_name)
        module_obj.__file__ = full_path_to_module
        globals()[module_name] = module_obj
        os.chdir(save_cwd)
    except:
        raise ImportError

            
def writeConfig(cfg,file):
    with open(file, 'w') as f:
        json.dump(cfg, f)
    return;
def loadConfig(cfg,file):
    if(os.path.isfile(file)):
        with open(file, 'r') as f:
            cfg2 = json.load(f);
            cfg.update(cfg2);
        return True;
    else:
        return False;  
def checkDirInput(dinput):
    if(os.path.isdir(dinput)):
        return True
    else:
        print "Error directory %s is not a directory" % dinput
        return False
def getDirInput(cfgName):
    print "%s ?:" % cfgName
    dirinput = raw_input();
    while(not ( checkDirInput(dirinput) )):
        print "%s ?:" % cfgName
        dirinput = raw_input();
    return dirinput;
def initGlobalConfig(cfg):
    print "Cef Remote Url?:"
    cfg[cef_vidyo_remote_url_cfg] = raw_input();
    print "Chromium Remote Url?:"
    cfg[chromium_vidyo_remote_url_cfg] = raw_input();
def initMachineConfig(cfg):
    print "Chromium Directory? "
    crm_dir = getDirInput("chromium_dir");
    cef_dir = getDirInput("cef_dir");
    build_dir = getDirInput("build_output_dir");
    newcfg = {};
    newcfg["chromium_dir"] = crm_dir;
    newcfg["cef_dir"] = cef_dir;    
   
    newcfg[local_build_number_cfg] = 0; 
    newcfg[build_output_dir_cfg] = build_dir;
    cfg.update(newcfg)

def increaseBuildNumber(machCfg):
    cur_build_num =  machCfg[local_build_number_cfg]

    cur_build_num = cur_build_num + 1;
    config[local_build_number_cfg] =   cur_build_num;
    newcfg = {};
    newcfg[local_build_number_cfg] = cur_build_num;
    machCfg.update(newcfg);
    print "Wiritng machine config after build number increase %s" % machCfg
    writeConfig(machCfg,machine_config_file);
def checkForRemote(repo,remoteName):
    aremote = repo.remotes[remoteName]
    if (aremote.exists() ):
        return True;
    else:
        return False;
def addRemote(repo,url,remoteName):
    assert checkForRemote(repo,remoteName), "Trying to add a remote that already exists on repo"
    new_remote = repo.create_remote(remoteName, url);
    assert new_remote.exists();
    new_remote.fetch();
    return new_remote;

    
def printGitInfo(infoRepo):
    remotes = infoRepo.remotes;
    tags = infoRepo.tags;
    heads = infoRepo.heads;
    current_head = infoRepo.head;
    is_dirty = infoRepo.is_dirty();
    untracked_files = infoRepo.untracked_files;
    description =  infoRepo.description;
    git_dir = infoRepo.git_dir;
    print " Git Repo Info dir: %s Description: %s \n remotes: %s \n tags: tags: %s \n heads: %s \n current_head: %s \n is_dirty: %s" % (git_dir,description,remotes,tags,heads,current_head,is_dirty)           

def checkoutHash(coRepo,hash):
        coRepo.fetch();
        
        build_branch = coRepo.create_head('build_branch', hash)
        coRepo.head.reference = build_branch;
        assert not repo.head.is_detached
        # reset the index and working tree to match the pointed-to commit
        coRepo.head.reset(index=True, working_tree=True)
        coRepo.pull();
        print "Done checking out hash: %s  current_head: %s "  % (hash,coRepo.head)
def checkoutBranchLatest(coRepo,branchname):
    vremote = coRepo.remotes[vidyo_remote_name]
    assert vremote.exists()
    vremote.fetch()
  
    remote = coRepo.remotes[vidyo_remote_name];
    assert remote.exists()
    remote.fetch();
    
    coRepo.create_head(branchname, remote.refs[branchname]).set_tracking_branch(remote.refs[branchname])
    remote.pull();
    print "Done checking out remote branch and latest Remote branch name %s current_head %s" % (branchname,coRepo.head)
    
    
def deleteBuildBranch(cefrepo,chrrepo):
    cefrepo.delete_head('build_branch');
    chrrepo.delete_head('build_branch');
def cleanup(cefrepo,chrrepo):
    deleteBuildBranch(cefrepo,chrrepo);            
def getBuildNumber():
    return config[local_build_number_cfg];         
def getChromeDir():
    return config[chrome_dir_cfg];    
def getCefDir():
    return config[cef_dir_cfg];
def getCefVidyoUrl():
    return config[cef_vidyo_remote_url_cfg];
def getChromeVidyoUrl():
    return config[chromium_vidyo_remote_url_cfg];
def getDistribDir():
    return config[build_output_dir_cfg];
def makeDistrib():
    dist_script_path = os.path.join(getCefDir(),'tools/make_distrib.py');
    print "Make distrib path: %s" % dist_script_path;
    os.chdir(getCefDir())
    call(['python',dist_script_path,"--output-dir",getDistribDir(),"--x64-build","--no-docs","--no-archive","--no-symbols","--ninja-build"])
    
def updateCefProjects():
    project_script_path = os.path.join(getCefDir(),"tools/gclient_hook.py");
    project_exec = "python"
    
    print "Cef Update projects script path: %s" % project_script_path
    call(['cd',getCefDir()])
    call([project_exec,project_script_path]);
   #import_file(project_script_path);
   #gclient_hook();
if (loadConfig(config,global_config_file)):
    print "Loaded global config file %s with config: %s" %(global_config_file, config)
else:
    print "Failed to load global config file %s - need to init config" % global_config_file
    initGlobalConfig(config);
    writeConfig(config,global_config_file);
    print "Wrote config %s to config file %s "  %(config, global_config_file)
if (loadConfig(config,machine_config_file)):
    print "Loaded  machine config file %s with config: %s" %(machine_config_file, config)
else:
    print "Failed to load machine config file %s - need to init config" % machine_config_file
    mch_cfg = {};
    initMachineConfig(mch_cfg);
    
    writeConfig(mch_cfg,machine_config_file);
    print "Wrote config %s to config file %s "  %(mch_cfg, machine_config_file)  
    increaseBuildNumber(mch_cfg);
    config.update(mch_cfg);
    print "Config after machine config loaded: %s" % config 
 

  
  
  
#parse cmd line parameters
# Parse command-line options.
disc = """
This is a build utility for building our custom CEF/Chromium by William Bittner.
"""

parser = OptionParser(description=disc)
# Assumes folder  setup base/depot_tools base/chromium/src/ /base/chromium/src/cef/
# Setup options.
parser.add_option('--cef-branch', dest='cef_branch',
                  help='The cef branch to pull latest from and build',default='')
parser.add_option('--chrome-branch', dest='chrome_branch', 
                  help='The chromium branch to pull loatest from and build', default='')
parser.add_option('--cef-commit-hash', dest='cef_hash',
                  help='Commit hash to build instead of the latest on a branch',
                  default='')
parser.add_option('--chrome-commit-hash',dest='chrome_hash',default="",help="Commit hash of chrome to build instead of the latest of a branch")



(options, args) = parser.parse_args()


#begin work  
chrome_repo = Repo(getChromeDir());

cef_repo = Repo(getCefDir());

# verify /add remote
if (checkForRemote(cef_repo,vidyo_remote_name)):
    print "Cef Repo vidyo remote verified"
else:
    remote_added = addRemote(cef_repo,getCefVidyoUrl(),vidyo_remote_name);
    assert checkForRemote(cef_repo,vidyo_remote_name);
    print "Cef Repo for vidyo has been added to remotes"
if(checkForRemote(chrome_repo,vidyo_remote_name)):
    print "Chrome repo remote verified"
else:
    remote_added = addRemote(chrome_repo,getChromeVidyoUrl(),vidyo_remote_name);
    assert checkForRemote(chrome_repo,vidyo_remote_name);
    print "Chrome Repo for vidyo has been added to remotes"
    
# checkout the latest    

if options.cef_branch is None:
    if options.cef_hash is None:
       print "You need to specify either a branch or a commit hash for the CEF to be built"
    else:
        checkoutHash(cef_repo,options.cef_hash);
else:
    checkoutBranchLatest(cef_repo,options.cef_branch);
            
if options.chrome_branch is None:
    if options.chrome_hash is None:
        print "You need to specify either a branch or commit hash for Chrome to be built on"
    else:
        checkoutHash(chrome_repo,options.chrome_hash)
else:
    checkoutBranchLatest(chrome_repo,options.chrome_branch)


#update the cef project files
#updateCefProjects()



#build the cef
print "Building build number: %s for platform %s" % (getBuildNumber(),platform)
build_type = "Debug";
os.chdir(getChromeDir())
#call(["cd", getChromeDir()]);
call(["ninja","-C","out/Debug","cefsimple", "cefclient"]);
call(["ninja","-C","out/Release", "cefsimple", "cefclient"]);




#build the distrib
makeDistrib()

#make the wrapper

#printGitInfo (chrome_repo)
#printGitInfo (cef_repo)



    

