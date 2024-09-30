import replicate


def create_image(prompt: str) -> str:
    input = {
        "prompt": prompt
        or "The world's largest black forest cake, the size of a building, surrounded by trees of the black forest"
    }

    # link
    output: str = replicate.run("black-forest-labs/flux-pro", input=input)

    return output
