from interactions import *
from interactions.api import models
import aiohttp
from ricerca_test import cerca as ricerca_avanzata
import asyncio
import json
import time
import datetime
import random


# COSTANTI
TOKEN = "TOKEN HERE"
ID_SERVER = # int(ID) HERE

ID_PLAYER = # int(ID) HERE
ID_RISERVA = # int(ID) HERE

COLORE_EMBED_DEFAULT = Color.from_rgb(r=104, g=155, b=242)

client = Client(token=TOKEN, intents=Intents.ALL)


@Task.create(IntervalTrigger(minutes=60))
async def promemoria_torneo():
    print("Mando il promemoria")
    with open("torneo.json", "r") as f:
        db_torneo = json.load(f)

    for nome_torneo in db_torneo:
        orario = db_torneo[nome_torneo]["ora"].split(":")
        giorno = db_torneo[nome_torneo]["data"].split("/")
        if int(time.strftime("%d")) == int(giorno[0]) and int(time.strftime("%m")) == int(giorno[1]):
            if int(time.strftime("%H")) == int(orario[0])-1:
                for partecipante_username in db_torneo[nome_torneo]["partecipanti"]:
                    gilda = client.get_guild(guild_id=ID_SERVER)
                    partecipante = utils.get(gilda.members, username=partecipante_username)
                    embed = Embed(title="Duellante, è il tuo momento!", description="Il torneo avrà inizio tra poco, preparati!", color=COLORE_EMBED_DEFAULT)
                    embed.set_image(url="https://media.tenor.com/Rals-7EOikIAAAAM/yu-gi-oh-vrains-anime.gif")
                    await partecipante.send(embed=embed)
        giorno_dopo = datetime.date.today() + datetime.timedelta(days=1)
        print(giorno_dopo.strftime("%d"))
        if int(giorno_dopo.strftime("%d")) == int(giorno[0]) and int(giorno_dopo.strftime("%m")) == int(giorno[1]):
            if int(time.strftime("%H")) == int(orario[0]):
                for partecipante_username in db_torneo[nome_torneo]["partecipanti"]:
                    gilda = client.get_guild(guild_id=ID_SERVER)
                    partecipante = utils.get(gilda.members, username=partecipante_username)
                    embed = Embed(title="Avviso", description="Duellante, il torneo si terrà domani. Ricorda di controllare che connessione, PC e webcam per eventuale Remote Duel siano funzionanti. Inoltre, se è previsto e non l'hai ancora fatto, ricorda di **inviare la Decklist** all'incaricato del torneo di domani.", color=COLORE_EMBED_DEFAULT)
                    embed.set_image(url="https://i.pinimg.com/originals/4b/20/42/4b2042b23c1e26e0d61553f60b9a9bda.gif")
                    await partecipante.send(embed=embed)

@listen()
async def on_startup():
    print("COMANDI SLASH PRONTI")
    if int(time.strftime("%M")) == 0:                           # Comincia a e 00
        promemoria_torneo.start()
    else:
        await asyncio.sleep(3600 - 60*int(time.strftime("%M")))
        promemoria_torneo.start()
    print("TASK DA 60 MINUTI IN ESECUZIONE")

async def cerca_url(name: str):
    name = name.replace("[", "").replace("(", "").replace(")", "").replace("{", "").replace("}", "")
    async with aiohttp.ClientSession() as session:
        trovata = False
        url = 'https://db.ygoprodeck.com/api/v7/cardinfo.php?name=' + name.lower().replace("&", "%26").replace("evil gemella", "evil★gemella") + '&language=it'
        async with session.get(url) as r:
            if r.status == 200:
                pre_js = await r.json()
                if "data" in pre_js:
                    trovata = True
        if not trovata:
            url = 'https://db.ygoprodeck.com/api/v7/cardinfo.php?name=' + name.lower().replace("&", "%26").replace("evil twin", "evil★twin")
            async with session.get(url) as r:
                if r.status == 200:
                    pre_js = await r.json()
                    if "data" in pre_js:
                        trovata = True
        if not trovata:
            n_it = None
            n_en = None
            n = None
            # Ciò solo se non trova prima col nome preciso
            async with session.get("https://db.ygoprodeck.com/api/v7/cardinfo.php?language=it") as r:
                print(r.status)
                if r.status == 200:
                    js = await r.json()
                    NOME = ricerca_avanzata(name.lower().replace("&", "%26").replace("evil gemella", "evil★gemella"), js)
                    n_it = NOME
                    print("[RISULTATO RICERCA ITA]", n_it)
            # Fa lo stesso con la lingua inglese e vede quale dei due casi è più calzante
            async with session.get("https://db.ygoprodeck.com/api/v7/cardinfo.php?") as r:
                print(r.status)
                if r.status == 200:
                    js = await r.json()
                    NOME = ricerca_avanzata(name.lower().replace("&", "%26").replace("evil gemella", "evil★gemella"), js)
                    n_en = NOME
                    print("[RISULTATO RICERCA ENG]", n_en)
            if n_it["di_quanto"] >= n_en["di_quanto"]:
                n = n_it["nome"]
                url = 'https://db.ygoprodeck.com/api/v7/cardinfo.php?name=' + n.lower().replace("&", "%26").replace("evil gemella", "evil★gemella") + '&language=it'
            else:
                n = n_en["nome"]
                url = 'https://db.ygoprodeck.com/api/v7/cardinfo.php?name=' + n.lower().replace("&", "%26").replace("evil twin", "evil★twin")

        print(url)
        return url

@slash_command(
        name="art",
        description="Artwork di una carta",
)
@slash_option(
    name="nome",
    description="fornire il nome completo in italiano o inglese",
    required=True,
    opt_type=OptionType.STRING
)
async def art(ctx: SlashContext, nome: str):
    placeholder = await ctx.send("Ricerca in corso...")
    url = await cerca_url(nome)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as r:
            if r.status == 200:
                js = await r.json()
                card_img = js['data'][0]['card_images'][0]['image_url_cropped']
                card_name = js['data'][0]['name']
                embed = Embed(description=f'Artwork di **{card_name}**')
                embed.set_image(url=card_img)
                await ctx.send(embed=embed)
                await ctx.delete(message=placeholder)


##########################################################################################################################

async def admin_check(ctx: BaseContext):
    try:
        admin_role = ctx.author.has_role(ctx.author.guild.get_role(673485367349084183)) 
        mod_role = ctx.author.has_role(ctx.author.guild.get_role(673485960725659649))
        rulings_expert = ctx.author.has_role(ctx.author.guild.get_role(673921679185018911))
        return rulings_expert or admin_role or mod_role
    except:
        perms = ctx.author.has_permission(Permissions.ADMINISTRATOR)
        mod_perms = ctx.author.has_permission(Permissions.MODERATE_MEMBERS)
        return perms or mod_perms

##########################################################################################################################

@slash_command(
        name="timer",
        description="Imposta un timer"
)
@slash_option(
    name="ruolo",
    description="Ruolo da menzionare a fine timer",
    required=True,
    opt_type=OptionType.ROLE
)
@slash_option(
    name="minuti",
    description="Durata del timer in minuti",
    required=False,
    opt_type=OptionType.INTEGER
)
@check(admin_check)
async def timer(ctx, ruolo: Role, minuti: int=None):
    if minuti == None:
        minuti = 45
    with open("timer.json", "r") as f:
        lista_timer = json.load(f)
        def get_timer_id():
            """Genera un ID di 4 cifre da assegnare a questo timer"""
            tid = str(random.randint(1000, 9999))
            if tid not in lista_timer:
                return tid
            else:
                return get_timer_id()

        timer_id = get_timer_id()
        ID = ruolo.mention
        info_fine = int(time.time() + minuti*60)
        info_embed = Embed(title="Turno", description=f"Fine turno alle <t:{info_fine}:t> (<t:{info_fine}:R>)")
        lista_timer[timer_id] = {
            "id": timer_id,
            "attivo": True,
            "ruolo": ruolo.mention,
            "minuti": minuti,
            "fine": f"<t:{info_fine}:t>"
        }
    with open("timer.json", "w") as f:
        json.dump(lista_timer, f, indent=4)
    
    await ctx.send(f'{ID}, il turno dalla durata complessiva di **{minuti} minuti** comincia ora', embed=info_embed, allowed_mentions=AllowedMentions.all())
    if minuti > 10:
        await asyncio.sleep(minuti * 60 - 600)

        if timer_id in json.load(open("timer.json", "r")):
            await ctx.channel.send(f'{ID}, 10 minuti rimanenti alla fine del turno', allowed_mentions=AllowedMentions.all())
        await asyncio.sleep(600)
        if timer_id in json.load(open("timer.json", "r")):
            await ctx.channel.send(f'{ID}, FINE TURNO', allowed_mentions=AllowedMentions.all())
    elif minuti <= 10:
        await ctx.channel.send(f'{ctx.author.mention}, il timer che è stato impostato è minore o uguale a 10 minuti, perciò riceverai un avviso solo alla scadenza.')
        await asyncio.sleep(minuti * 60)
        if timer_id in json.load(open("timer.json", "r")):
            await ctx.channel.send(f'{ID}, FINE TURNO', allowed_mentions=AllowedMentions.all())

    with open("timer.json", "r") as f:
        lista_timer = json.load(f)
        if timer_id in lista_timer:
            del lista_timer[timer_id]
    with open("timer.json", "w") as f:
        json.dump(lista_timer, f, indent=4)

@slash_command(
        name="lista_timer",
        description="Mostra la lista dei timer attivi"
)
@check(admin_check)
async def lista_timer(ctx: SlashContext):
    with open("timer.json", "r") as f:
        lista_timer = json.load(f)

        if len(lista_timer) == 0:
            await ctx.send("❕Nessun timer in corso")

        for elemento_timer in lista_timer:
            embed = Embed(title=f"""Timer da {lista_timer[elemento_timer]["minuti"]} minuti""", description=f"""Ruolo: {lista_timer[elemento_timer]["ruolo"]}
        Scadenza: {lista_timer[elemento_timer]["fine"]}""")
            embed.add_field(name="ID Timer", value=lista_timer[elemento_timer]["id"])
            comp_chiudi = Button(
                custom_id="comp_chiudi",
                style=ButtonStyle.RED,
                label="Interrompi"
            )
            await ctx.send(embed=embed, components=comp_chiudi)

@component_callback("comp_chiudi")
async def chiudi_timer(ctx: SlashContext):
    with open("timer.json", "r") as f:
        lista_timer = json.load(f)
        val = ctx.message.embeds[0].fields[0].value
        if val in lista_timer:
            del lista_timer[val]
            await ctx.send("☑️ Timer interrotto")
    with open("timer.json", "w") as f:
        json.dump(lista_timer, f, indent=4)

##########################################################################################################################


@component_callback("comp_iscriviti")
async def iscrizione(ctx: SlashContext):
    with open("torneo.json", "r") as f:
        db = json.load(f)
        nome_torneo = ctx.message.embeds[0].title
        lista = db[nome_torneo]["partecipanti"]
        lista_riserve = db[nome_torneo]["riserve"]
        posti_rimanenti = db[nome_torneo]["max_partecipanti"] - len(lista)
        try:
            ruolo_player = ctx.author.guild.get_role(int(db[nome_torneo]["ruolo_player"].replace("<@&", "").replace(">", "")))
            ruolo_riserva = ctx.author.guild.get_role(int(db[nome_torneo]["ruolo_riserva"].replace("<@&", "").replace(">", "")))
        
            if not ctx.author.username in lista:
                if posti_rimanenti > 0:
                    lista.append(ctx.author.username)
                    await ctx.author.add_role(role=ruolo_player)
                    await ctx.send(f"""☑️ Iscritto come {ctx.author.mention} al torneo "**{db[nome_torneo]["nome"]}**" """)
                else:
                    if not ctx.author.username in lista_riserve:
                        lista_riserve.append(ctx.author.username)
                        await ctx.author.add_role(role=ruolo_riserva)
                        await ctx.send(f"""❕ Posti finiti!\nIscritto come riserva (giocatore: {ctx.author.mention}) al torneo "**{db[nome_torneo]["nome"]}**" """)
                    else:
                        await ctx.send(f"""❗ {ctx.author.mention}, il tuo nome compare già nell'elenco delle riserve""")
            else:
                await ctx.send(f"""❗ {ctx.author.mention}, il tuo nome compare già nell'elenco degli iscritti""")

        except AttributeError:
                await ctx.send(embed=Embed(title="Attenzione", description="Si prega di procedere all'iscrizione nel canale dedicato del Server."))
    with open("torneo.json", "w") as f:
        json.dump(db, f, indent=4)

@component_callback("comp_spettatore")
async def spectate(ctx: SlashContext):
    with open("torneo.json", "r") as f:
        db = json.load(f)
    nome_torneo = ctx.message.embeds[0].title
    ruolo_spettatore = ctx.author.guild.get_role(int(db[nome_torneo]["ruolo_spettatore"].replace("<@&", "").replace(">", "")))
    if not ctx.author.has_role(ruolo_spettatore):
        await ctx.author.add_role(role=ruolo_spettatore)
        await ctx.send(f"""☑️ {ctx.author.mention}, parteciperai come __spettatore__ al torneo "**{db[nome_torneo]["nome"]}**" """)
    else:
        await ctx.author.remove_role(role=ruolo_spettatore)
        await ctx.send(f"""☑️ {ctx.author.mention}, non sarai più __spettatore__ di questo torneo "**{db[nome_torneo]["nome"]}**" """)

@component_callback("comp_annulla_iscrizione")
async def annulla_iscrizione(ctx: SlashContext):
    with open("torneo.json", "r") as f:
        db = json.load(f)
        nome_torneo = ctx.message.embeds[0].title
        lista = db[nome_torneo]["partecipanti"]
        lista_riserve = db[nome_torneo]["riserve"]
        
        try:
            ruolo_player = ctx.author.guild.get_role(int(db[nome_torneo]["ruolo_player"].replace("<@&", "").replace(">", "")))
            ruolo_riserva = ctx.author.guild.get_role(int(db[nome_torneo]["ruolo_riserva"].replace("<@&", "").replace(">", "")))
        
            if ctx.author.username in lista:
                lista.remove(ctx.author.username)
                await ctx.author.remove_role(role=ruolo_player)
                await ctx.send(f"""☑️ Iscrizione al torneo annullata per il giocatore {ctx.author.username}""")
                # Si scala
                posti_rimanenti = db[nome_torneo]["max_partecipanti"] - len(db[nome_torneo]["partecipanti"])
                print(posti_rimanenti)
                if posti_rimanenti > 0 and len(lista_riserve) != 0:
                    prev = lista_riserve[0]
                    db[nome_torneo]["riserve"].remove(prev)
                    db[nome_torneo]["partecipanti"].append(prev)
                    utens = utils.get(ctx.guild.members, username=prev)
                    await utens.remove_role(role=ruolo_riserva)
                    await utens.add_role(role=ruolo_player)
                    await ctx.send(f"{utens.mention} aggiunto ai partecipanti")
                    await utens.send("Sei passato da riserva a partecipante per il prossimo torneo!")
            elif ctx.author.username in lista_riserve:
                lista_riserve.remove(ctx.author.username)
                await ctx.author.remove_role(role=ruolo_riserva)
                await ctx.send(f"""☑️ Iscrizione al torneo come riserva annullata per il giocatore {ctx.author.username}""")
            else:
                await ctx.send(f"""❗ {ctx.author.mention}, il tuo nome non compare né nell'elenco degli iscritti né in quello delle riserve""")
        
        except AttributeError:
            await ctx.send(embed=Embed(title="Attenzione", description="Si prega di cancellare l'iscrizione nel canale dedicato del Server."))
    with open("torneo.json", "w") as f:
        json.dump(db, f, indent=4)

@slash_command(
        name="torneo",
        description="Visualizza il prossimo torneo"
)
async def torneo(ctx: SlashContext):
    with open("torneo.json", "r") as f:
        db = json.load(f)
        if len(db) == 0:
            await ctx.send("❕Nessun torneo previsto")
        for nome_torneo in db:
            posti_rimanenti = db[nome_torneo]["max_partecipanti"] - len(db[nome_torneo]["partecipanti"])
            embed = Embed(title=db[nome_torneo]["nome"], description=f"""Torneo in data {db[nome_torneo]["data"]}, ore {db[nome_torneo]["ora"]}\nMassimo di partecipanti: {db[nome_torneo]["max_partecipanti"]}\n**Posti rimanenti**: {posti_rimanenti}""", color=Color.from_rgb(r=104, g=155, b=242))
            embed.set_footer(text="Se è previsto l'invio della Decklist, comparirà un simbolo accanto al nome di coloro ai quali la lista è stata validata", icon_url="https://static.wikia.nocookie.net/yugioh/images/c/cc/IN4-M8.png/revision/latest?cb=20200508114005")

            partecipanti_grezzi = [utils.get(ctx.guild.members, username=par) if utils.get(ctx.guild.members, username=par) != None else par for par in db[nome_torneo]["partecipanti"]]
            riserve_grezze = [utils.get(ctx.guild.members, username=ris) if utils.get(ctx.guild.members, username=ris) != None else ris for ris in db[nome_torneo]["riserve"]]

            
            for p in partecipanti_grezzi:
                if "lista_inviata" in db[nome_torneo]:
                    try:
                        if p.username in db[nome_torneo]["lista_inviata"]:
                            partecipanti_grezzi[partecipanti_grezzi.index(p)] = f"{p.mention} | ☑️"
                        elif p.username != None:
                            partecipanti_grezzi[partecipanti_grezzi.index(p)] = f"{p.mention}"
                    except Exception:
                        pass
                else:
                    if type(p) == Member:
                        partecipanti_grezzi[partecipanti_grezzi.index(p)] = f"{p.mention}"
                        # TODO: CONTINUARE E TESTARE
            for r in riserve_grezze:
                if "lista_inviata" in db[nome_torneo]:
                    try:
                        if r.username in db[nome_torneo]["lista_inviata"]:
                            riserve_grezze[riserve_grezze.index(r)] = f"{r.mention} | ☑️"
                        elif r.username != None:
                            riserve_grezze[riserve_grezze.index(r)] = f"{r.mention}"
                    except:
                        pass
                else:
                    if type(r) == Member:
                        riserve_grezze[riserve_grezze.index(r)] = f"{r.mention}"
            
            partecipanti = "Nessun partecipante"
            riserve = "Nessuna riserva"
            if db[nome_torneo]["partecipanti"]:
                print(partecipanti_grezzi)
                partecipanti = "\n".join(partecipanti_grezzi)
            else:
                partecipanti = "Nessun partecipante"
            if db[nome_torneo]["riserve"]:
                riserve = "\n".join(riserve_grezze)
            else:
                riserve = "Nessuna riserva"
            
            embed.add_field(name="Partecipanti", value=partecipanti)
            embed.add_field(name="Riserve", value=riserve)

            comp_iscriviti = Button(
                custom_id="comp_iscriviti",
                style=ButtonStyle.GREEN,
                label="Iscriviti"
            )
            comp_spettatore = Button(
                custom_id="comp_spettatore",
                style=ButtonStyle.BLUE,
                label="Spettatore"
            )
            comp_annulla_iscrizione = Button(
                custom_id="comp_annulla_iscrizione",
                style=ButtonStyle.RED,
                label="Annulla iscrizione"
            )
            if ctx.author.username in db[nome_torneo]["partecipanti"] or ctx.author.username in db[nome_torneo]["riserve"]:
                comp_iscriviti.disabled = True
            else:
                comp_annulla_iscrizione.disabled = True

            comps = [ActionRow(comp_annulla_iscrizione, comp_iscriviti)]
            if "ruolo_spettatore" in db[nome_torneo]:
                comps = [ActionRow(comp_annulla_iscrizione, comp_spettatore, comp_iscriviti)]
            await ctx.send(embed=embed, components=comps)
    with open("torneo.json", "w") as f:
        json.dump(db, f, indent=4)

@slash_command(
        name="organizza_torneo",
        description="[Solo admin] Organizza il prossimo torneo"
)
@slash_option(
    name="nome",
    description="Nome del torneo",
    required=True,
    opt_type=OptionType.STRING
)
@slash_option(
    name="giorno",
    description="Giorno del torneo (inserire il numero del giorno, quindi il numero del mese nell'opzione successiva)",
    required=True,
    opt_type=OptionType.INTEGER,
    min_value=1,
    max_value=31
)
@slash_option(
    name="mese",
    description="Mese del torneo (inserire il numero del mese; es. 1: gennaio, 12: dicembre)",
    required=True,
    opt_type=OptionType.INTEGER,
    min_value=1,
    max_value=12
)
@slash_option(
    name="ora",
    description="Orario del torneo (inserire il numero dell'ora, quindi il numero dei minuti nell'opzione successiva)",
    required=True,
    opt_type=OptionType.INTEGER,
    min_value=0,
    max_value=24
)
@slash_option(
    name="minuti",
    description="Minuti dell'orario (es. 00; 30)",
    required=True,
    opt_type=OptionType.INTEGER,
    min_value=0,
    max_value=59
)
@slash_option(
    name="posti",
    description="Numero dei posti del torneo (riserve escluse)",
    required=True,
    opt_type=OptionType.INTEGER
)
@slash_option(
    name="ruolo_player",
    description="Ruolo dei giocatori di questo torneo",
    required=True,
    opt_type=OptionType.ROLE
)
@slash_option(
    name="ruolo_riserva",
    description="Ruolo delle riserve di questo torneo",
    required=True,
    opt_type=OptionType.ROLE
)
@slash_option(
    name="ruolo_spettatore",
    description="[OPZIONALE] Ruolo degli spettatori di questo torneo (Remote Duel)",
    required=False,
    opt_type=OptionType.ROLE
)
@check(admin_check)
async def organizza_torneo(ctx: SlashContext, nome: str, giorno: int, mese: int, ora: int, minuti: int, posti: int, ruolo_player: Role, ruolo_riserva: Role, ruolo_spettatore: Role=None):
    with open("torneo.json", "r") as f:
        db = json.load(f)
        if minuti == 0:
            minuti = "00"
        # posti -> max_partecipanti
        db[nome] = {
            "nome": nome,
            "data": f"{giorno}/{mese}",
            "ora": f"{ora}:{minuti}",
            "max_partecipanti": posti,
            "partecipanti": [],
            "riserve": [],
            "ruolo_player": ruolo_player.mention,
            "ruolo_riserva": ruolo_riserva.mention
        }
        if ruolo_spettatore is not None:
            db[nome]["ruolo_spettatore"] = ruolo_spettatore.mention
        await ctx.send("☑️ Torneo organizzato; per ottenere informazioni o iscriversi, usare il comando /torneo")
    with open("torneo.json", "w") as f:
        json.dump(db, f, indent=4)

@slash_command(
        name="elimina_torneo",
        description="Elimina un torneo"
)
@slash_option(
    name="nome_torneo",
    description="Il nome del torneo da cancellare (case sensitive)",
    opt_type=OptionType.STRING,
    required=True
)
@check(admin_check)
async def elimina_torneo(ctx: SlashContext, nome_torneo):
    with open("torneo.json", "r") as f:
        db = json.load(f)

        # Rimuove il ruolo di player e riserva a chi lo ha

        ruolo_player = ctx.author.guild.get_role(int(db[nome_torneo]["ruolo_player"].replace("<@&", "").replace(">", "")))
        ruolo_riserva = ctx.author.guild.get_role(int(db[nome_torneo]["ruolo_riserva"].replace("<@&", "").replace(">", "")))

        for membro in ruolo_player.members:
            try:
                await membro.remove_role(role=ruolo_player)
                print(f"[RUOLI] Ruolo PLAYER rimosso a {membro.username}")
            except:
                print(f"[RUOLI] Ruolo PLAYER NON RIMOSSO a {membro.username}")
        for membro_riserva in ruolo_riserva.members:
            try:
                await membro_riserva.remove_role(role=ruolo_riserva)
                print(f"[RUOLI] Ruolo RISERVA rimosso a {membro_riserva.username}")
            except:
                print(f"[RUOLI] Ruolo RISERVA NON RIMOSSO a {membro_riserva.username}")
        
        if nome_torneo in db:
            del db[nome_torneo]
            await ctx.send(f"☑️ Torneo {nome_torneo} eliminato correttamente")
        else:
            await ctx.send(f"❗ Torneo {nome_torneo} non presente tra quelli registrati (consultare /torneo per la lista dei tornei registrati)")

    with open("torneo.json", "w") as f:
        json.dump(db, f, indent=4)

@slash_command(
        name="iscrivi_player",
        description="Iscrivi un giocatore al torneo selezionato"
)
@slash_option(
    name="nome_torneo",
    description="Il nome del torneo a cui iscrivere il giocatore",
    opt_type=OptionType.STRING,
    required=True
)
@slash_option(
    name="giocatore",
    description="Chi iscrivere",
    opt_type=OptionType.USER,
    required=True
)
@slash_option(
    name="ruolo",
    description="Scegliere se iscriverlo come giocatore o come riserva",
    opt_type=OptionType.STRING,
    choices=[
        SlashCommandChoice(name="Player", value="partecipanti"),
        SlashCommandChoice(name="Riserva", value="riserve")
    ],
    required=True
)
@check(admin_check)
async def iscrivi_player(ctx: SlashCommand, nome_torneo: str, giocatore: User, ruolo: str):
    with open("torneo.json", "r") as f:
        db = json.load(f)
        if ruolo == "partecipanti":
            ruolo_selezionato = ctx.author.guild.get_role(int(db[nome_torneo]["ruolo_player"].replace("<@&", "").replace(">", "")))
        else:
            ruolo_selezionato = ctx.author.guild.get_role(int(db[nome_torneo]["ruolo_riserva"].replace("<@&", "").replace(">", "")))
        if nome_torneo in db:
            if not giocatore.username in db[nome_torneo][ruolo]:
                db[nome_torneo][ruolo].append(giocatore.username)
                await giocatore.add_role(role=ruolo_selezionato)
                await ctx.send(f"☑️ {giocatore.mention} iscritto al torneo {nome_torneo} con il ruolo di {ruolo_selezionato.mention}")  # di default menziona solo membri
            else:
                await ctx.send(f"❕ {giocatore.mention} risulta già iscritto al torneo {nome_torneo}")
        else:
            await ctx.send("❗ Torneo non trovato")

    with open("torneo.json", "w") as f:
        json.dump(db, f)

@slash_command(
        name="annulla_iscrizione_player",
        description="Annulla l'iscrizione di un giocatore dal torneo selezionato"
)
@slash_option(
    name="nome_torneo",
    description="Il nome del torneo da cui eliminare il giocatore",
    opt_type=OptionType.STRING,
    required=True
)
@slash_option(
    name="giocatore",
    description="A chi annullare l'iscrizione",
    opt_type=OptionType.USER,
    required=False
)
@slash_option(
    name="vecchio_giocatore",
    description="Username del giocatore non più nel Server",
    opt_type=OptionType.STRING,
    required=False
)
@check(admin_check)
async def annulla_iscrizione_player(ctx: SlashCommand, nome_torneo: str, giocatore: User=None, vecchio_giocatore: str=None):
    if giocatore == None and vecchio_giocatore == None:
        await ctx.send("❗ Fornire flmeno un valore tra `giocatore` e `vecchio_giocatore`")
        return False
    elif vecchio_giocatore != None:
        giocatore_username = vecchio_giocatore
    elif giocatore != None:
        giocatore_username = giocatore.username
    with open("torneo.json", "r") as f:
        db = json.load(f)

        ruolo_player = ctx.author.guild.get_role(int(db[nome_torneo]["ruolo_player"].replace("<@&", "").replace(">", "")))
        ruolo_riserva = ctx.author.guild.get_role(int(db[nome_torneo]["ruolo_riserva"].replace("<@&", "").replace(">", "")))

        if nome_torneo in db:
            if giocatore_username in db[nome_torneo]["partecipanti"]:
                ruolo_selezionato = ruolo_player
                db[nome_torneo]["partecipanti"].remove(giocatore_username)
                if giocatore != None:
                    await giocatore.remove_role(role=ruolo_selezionato)
                await ctx.send(f"""☑️ Iscrizione al torneo annullata per il giocatore {giocatore_username}""")

                posti_rimanenti = db[nome_torneo]["max_partecipanti"] - len(db[nome_torneo]["partecipanti"])
                if posti_rimanenti > 0 and len(db[nome_torneo]["riserve"]) != 0:
                    prev = db[nome_torneo]["riserve"][0]
                    db[nome_torneo]["riserve"].remove(prev)
                    db[nome_torneo]["partecipanti"].append(prev)
                    utens = utils.get(ctx.guild.members, username=prev)
                    await utens.remove_role(role=ruolo_riserva)
                    await utens.add_role(role=ruolo_player)
                    await ctx.send(f"☑️ {utens.mention} aggiunto ai partecipanti")
                    await utens.send("Sei passato da riserva a partecipante per il prossimo torneo!")

            elif giocatore_username in db[nome_torneo]["riserve"]:
                ruolo_selezionato = ruolo_riserva
                db[nome_torneo]["riserve"].remove(giocatore_username)
                if giocatore != None:
                    await giocatore.remove_role(role=ruolo_selezionato)
                await ctx.send(f"""☑️ Iscrizione al torneo annullata per il giocatore {giocatore_username}""")
            else:
                await ctx.send(f"❕ {giocatore_username} non risulta iscritto al torneo {nome_torneo}")
        else:
            await ctx.send("❗ Torneo non trovato")

    with open("torneo.json", "w") as f:
        json.dump(db, f)

@slash_command(
        name="lista_inviata",
        description="Conferma che un giocatore ha inviato la Decklist per partecipare al torneo"
)
@slash_option(
    name="giocatore",
    description="A chi annullare l'iscrizione",
    opt_type=OptionType.USER,
    required=True
)
@slash_option(
    name="annulla",
    description="Se si desidera annullare la conferma di invio della lista",
    opt_type=OptionType.BOOLEAN,
    required=False
)
@check(admin_check)
async def lista_inviata(ctx: SlashCommand, giocatore: User, annulla: bool = False):
    fatto = False
    with open("torneo.json", "r") as f:
        db = json.load(f)
    if len(db) == 0:
        await ctx.send("❗ Nessun torneo previsto")
    for nome_torneo in db:
        if giocatore.username in db[nome_torneo]["partecipanti"]:
            if not "lista_inviata" in db[nome_torneo]:
                db[nome_torneo]["lista_inviata"] = []
            if not annulla:
                db[nome_torneo]["lista_inviata"].append(giocatore.username)
                fatto = True
                await ctx.send(f"☑️ Lista confermata per il giocatore __{giocatore.mention}__ al torneo {nome_torneo}")
            else:
                db[nome_torneo]["lista_inviata"].remove(giocatore.username)
                fatto = True
                await ctx.send(f"☑️ Conferma di lista annullata per il giocatore __{giocatore.mention}__ al torneo {nome_torneo}")
    if not fatto:
        await ctx.send(f"❗ Il giocatore __{giocatore.mention}__ non è iscritto a nessun torneo")
    with open("torneo.json", "w") as f:
        json.dump(db, f, indent=4)


client.start()