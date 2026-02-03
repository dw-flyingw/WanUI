# ============================================================
# ANIMATE MODEL - Character and Background Replacement in Video
# Replace a person in a video with another person from a photo,
# and optionally replace the background with a custom image
# ============================================================
#
# Creates the following files in OUTPUT_FOLDER:
#   - src_pose.mp4   (pose skeleton extracted from source video)
#   - src_face.mp4   (face crops from source video)
#   - src_bg.mp4     (background with person removed)
#   - src_mask.mp4   (person segmentation mask)
#   - src_ref.png    (reference photo of replacement person)

# STEP 1: Preprocessing - Extract pose/face/mask/background from source video
EXAMPLE_DIR="$(cd "$(dirname "$0")" && pwd)"
(cd /home/users/wrightda/src/Wan2.2/wan/modules/animate/preprocess && python preprocess_data.py --ckpt_path /opt/huggingface/Wan2.2-Animate-14B/process_checkpoint --video_path "${EXAMPLE_DIR}/video.mp4" --refer_path "${EXAMPLE_DIR}/image.jpg" --save_path "${EXAMPLE_DIR}/output" --replace_flag)



# STEP 2: Generation - Run animate model with character replacement
torchrun --nproc_per_node=2 /home/users/wrightda/src/Wan2.2/generate.py --task animate-14B --size 1280*720 --ckpt_dir /opt/huggingface/Wan2.2-Animate-14B --dit_fsdp --t5_fsdp --ulysses_size 2 --replace_flag --refert_num 5 --src_root_path "${EXAMPLE_DIR}/output" --audio "${EXAMPLE_DIR}/output/audio.mp3" --prompt "The person from the reference image replaces the talk show host, performing the same speaking gestures and expressive movements in the TV studio setting, seamlessly matching the original motion and lighting."

