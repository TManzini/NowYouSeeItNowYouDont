::Set the python path
set PYTHONPATH=./src/

::Install dependencies
pip install -r requirements.txt

::Select the directories where the data necessary for the replication should be stored
set data_download_directory="TODO - CHANGE TO WHERE YOU WANT TO DOWNLOAD THE DATA"
set outputs_folder="TODO - CHANGE TO WHERE YOU WANT TO WRITE THE OUTPUTS"

::Login to the huggingface command line interface
huggingface-cli login

::Download the sUAS, Satellite, and metadata data necessary for the replication.
::The replication relies on data from revision: 58f0d5ea2544dec8c126ac066e236943f26d0b7e
huggingface-cli download CRASAR/CRASAR-U-DROIDs --include "*SATELLITE/building_damage_assessment/*.json" --repo-type dataset --local-dir %data_download_directory% --revision 58f0d5ea2544dec8c126ac066e236943f26d0b7e
huggingface-cli download CRASAR/CRASAR-U-DROIDs --include "*sUAS/building_damage_assessment/*.json" --repo-type dataset --local-dir %data_download_directory% --revision 58f0d5ea2544dec8c126ac066e236943f26d0b7e
huggingface-cli download CRASAR/CRASAR-U-DROIDs --include "statistics.csv" --repo-type dataset --local-dir %data_download_directory% --revision 58f0d5ea2544dec8c126ac066e236943f26d0b7e

::Select & organize the data that will be used for the replication from what was downloaded...
set output_stats_file=%outputs_folder%/stats.csv
set output_suas_path_map=%outputs_folder%/output_suas_path_map.json
set output_satellite_path_map=%outputs_folder%/output_satellite_path_map.json
python ./src/make_metadata_files.py --crasar_u_droids_dir %data_download_directory% ^
                                    --output_stats_file %output_stats_file% ^
                                    --output_suas_path_map %output_suas_path_map% ^
                                    --output_satellite_path_map %output_satellite_path_map%

::Run the replication...
python ./src/main.py --satellite_annotations_path_map %output_satellite_path_map% ^
                     --drone_annotations_path_map %output_suas_path_map% ^
                     --output_folder_path %outputs_folder% ^
                     --multiview_stats_file_path %output_stats_file%
