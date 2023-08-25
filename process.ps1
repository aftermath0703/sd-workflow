$url=""
$task_path="sample/task.txt"
$process_dir="sample/process"
$output_root="output"

$ext_args = [System.Collections.ArrayList]::new()
if($url) {
    [void]$ext_args.Add("--url=$url")
}

python process.py --task_path=$task_path --process_dir=$process_dir --output_root=$output_root $ext_args

Write-Output "finished"
Read-Host | Out-Null ;