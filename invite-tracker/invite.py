import discord, asqlite
from discord.ext.commands import Bot

intents = discord.Intents.all()
bot = Bot(command_prefix=".", intents=intents)

invites = {}


def find_inv(invite_list, code):
    for invite in invite_list:
        if invite.code == code:
            return invite


async def fetch(query: str, *data):
    con = await asqlite.connect("invite.db")
    cur = await con.cursor()
    await cur.execute(query, data)
    result = await cur.fetchall()
    await cur.close()
    await con.close()
    return result


bot.fetch = fetch


@bot.event
async def on_ready():
    print(f"Logged in: {bot.user}")
    await bot.load_extension("jishaku")
    for guild in bot.guilds:
        invites[guild.id] = await guild.invites()


@bot.event
async def on_member_join(member):
    try:
        print("hi")
        log_channel = bot.get_channel(
            int(
                (
                    await fetch(
                        "SELECT channel FROM log WHERE guild = $1;", member.guild.id
                    )
                )[0].channel
            )
        )
        print(log_channel)
        embed = discord.Embed(
            description=f"**{member}** joined the server",
            color=0x00FF00,
            tiemstamp=discord.utils.utcnow(),
        )
        embed.set_author(icon_url=member.display_avatar.url, name=str(member))
        embed.set_footer(text=f"ID: {member.id}")
        inv_before = invites[member.guild.id]
        inv_after = await member.guild.invites()
        invites[member.guild.id] = inv_after
        for invite in inv_before:
            print(invite, invite.uses)
            if invite.uses < find_inv(inv_after, invite.code).uses:
                embed.add_field(
                    name="Used invite",
                    value=f"Inviter: {invite.inviter.mention} (`{invite.inviter}` | `{invite.inviter.id}`)\nCode: `{invite.code}`\nUses: `{invite.uses}`",
                )
                break
        await log_channel.send(embed=embed)
    except Exception as e:
        print(e)


@bot.event
async def on_member_remove(member):
    try:
        log_channel = bot.get_channel(
            int(
                (
                    await fetch(
                        "SELECT channel FROM log WHERE guild = $1;", member.guild.id
                    )
                )[0].channel
            )
        )
        embed = discord.Embed(
            description=f"**{member}** left the server",
            color=0x00FF00,
            timestamp=discord.utils.utcnow(),
        )
        embed.set_author(icon_url=member.display_avatar.url, name=str(member))
        embed.set_footer(text=f"ID: {member.id}")
        inv_before = invites[member.guild.id]
        inv_after = await member.guild.invites()
        invites[member.guild.id] = inv_after
        for invite in inv_before:
            if invite.uses > find_inv(inv_after, invite.code).uses:
                embed.add_field(
                    name="Used invite",
                    value=f"Inviter: {invite.inviter.mention} (`{invite.inviter}` | `{invite.inviter.id}`)\nCode: `{invite.code}`\nUses: `{invite.uses}`",
                )
                break
        await log_channel.send(embed=embed)

    except:
        pass


@bot.command()
async def setlogchannel(ctx, channel: discord.TextChannel):
    """Set the log channel for the invite tracker."""

    await fetch(
        "INSERT INTO log VALUES ($1, $2) ON CONFLICT (guild) DO UPDATE SET channel = $1;",
        channel.id,
        ctx.guild.id,
    )
    await ctx.send(f"Successfully set the log channel to {channel.mention}.")


bot.run("")
