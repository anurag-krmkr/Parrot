def get_command_signature(command) -> str:
    return f'[p]{command.name}{"|" if command.aliases else ""}{"|".join(command.aliases if command.aliases else "")} {command.signature}'


def common_command_formatting(embed_like, command):
    embed_like.title = f"Help with command `{command.name}`"

    embed_like.description = f"```\n{command.help if command.help else 'Help not available... :('}\n```"
    embed_like.add_field(
        name="Usage", value=f"```\n{get_command_signature(command)}\n```")
    embed_like.add_field(
        name="Aliases",
        value=
        f"```\n{', '.join(command.aliases if command.aliases else '')}\n```")