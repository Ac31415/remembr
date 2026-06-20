from mlx_vlm.utils import load

model_path = "mlx-community/llava-llama-3-8b-v1_1-8bit"
model, processor = load(model_path)
print(processor.__dict__)

prompt = processor.tokenizer.apply_chat_template(
    [{"role": "user", "content": f"<image>What are these?"}],
    tokenize=False,
    add_generation_prompt=True,
)
print(prompt)