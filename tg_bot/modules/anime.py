import requests, jikanpy, textwrap, datetime
from telegram.ext import CommandHandler, run_async
from telegram import Message, Update, Bot, InlineKeyboardMarkup, InlineKeyboardButton
from tg_bot import dispatcher
from telegram import ParseMode

#Backport of fromisoformat function from python 3.7
from backports.datetime_fromisoformat import MonkeyPatch
MonkeyPatch.patch_fromisoformat()

info_btn = "More Information"
kaizoku_btn = "Kaizoku ☠️"
kayo_btn = "Kayo 🏴‍☠️"

def getKitsu(mal):
    # get kitsu id from mal id
    link = f'https://kitsu.io/api/edge/mappings?filter[external_site]=myanimelist/anime&filter[external_id]={mal}'
    result = requests.get(link).json()['data'][0]['id']
    link = f'https://kitsu.io/api/edge/mappings/{result}/item?fields[anime]=slug'
    kitsu = requests.get(link).json()['data']['id']
    return(kitsu)

def getPosterLink(mal):
    # grab poster from kitsu
    kitsu = getKitsu(mal)
    image = requests.get(f'https://kitsu.io/api/edge/anime/{kitsu}').json()
    return(image['data']['attributes']['posterImage']['original'])

def getBannerLink(mal):
    # try getting kitsu backdrop
    kitsu = getKitsu(mal)
    image = f'http://media.kitsu.io/anime/cover_images/{kitsu}/original.jpg'
    response = requests.get(image)
    if response.status_code == 200: return(image)
    # try getting anilist banner
    query = '''
    query ($idMal: Int){
        Media(idMal: $idMal){
            bannerImage
        }
    }
    '''
    image = requests.post('https://graphql.anilist.co', json={'query': query, 'variables': {'idMal': int(mal)}}).json()['data']['Media']['bannerImage']
    if image: return(image)
    # use the poster from kitsu
    return(getPosterLink(mal))

@run_async
def anime(bot: Bot, update: Update):
    
    message = update.effective_message
    args = message.text.strip().split(" ", 1)
    try:
        search_query = args[1]
    except:
        update.effective_message.reply_text("Format : /anime <animename>")
        return

    progress_message = update.effective_message.reply_text("Searching.... ")
    jikan = jikanpy.jikan.Jikan()
    search_result = jikan.search("anime", search_query)
    first_mal_id = search_result["results"][0]["mal_id"]
    
    anime = jikan.anime(first_mal_id)
    image = getBannerLink(first_mal_id)

    caption = f"[{anime['title']}]({anime['url']})"

    if anime['title_japanese']:
        caption += f" ({anime['title_japanese']})\n"
    else:
        caption += "\n"

    alternative_names = [anime['title_english']]
    alternative_names.extend(anime['title_synonyms'])

    if alternative_names and None not in alternative_names:
        alternative_names_string = ", ".join(alternative_names)
        caption += f"\nAlternative Names : `{alternative_names_string}`"

    genre_string = ', '.join([genre_info['name'] for genre_info in anime['genres']])
    studio_string = ', '.join([studio_info['name'] for studio_info in anime['studios']])
    producer_string = ', '.join([producer_info['name'] for producer_info in anime['producers']])
    
    synopsis = anime['synopsis'].split(" ", 60)

    try:
        synopsis.pop(60)
    except IndexError:
        pass

    synopsis_string = ' '.join(synopsis)

    caption += textwrap.dedent(f"""
    *Type*: `{anime['type']}`
    *Status*: `{anime['status']}`
    *Aired*: `{anime['aired']['string']}`
    *Episodes*: `{anime['episodes']}`
    *Premiered*: `{anime['premiered']}`
    *Duration*: `{anime['duration']}`
    *Genres*: `{genre_string}`
    *Studios*: `{studio_string}`
    *Producers*: `{producer_string}`

    📖 *Synopsis*: {synopsis_string}... [read more]({anime['url']}).

    _Interested? Download an encode from:
    Search an encode on_
    """)

    kaizoku = f"https://animekaizoku.com/?s={search_query}"
    kayo = f"https://animekayo.com/?s={search_query}"
    buttons = [
        [InlineKeyboardButton(kaizoku_btn, url=kaizoku), InlineKeyboardButton(kayo_btn, url=kayo)]
    ]

    progress_message.delete()
    update.effective_message.reply_photo(photo=image, caption=caption, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=False)

@run_async
def manga(bot: Bot, update: Update):

    message = update.effective_message
    args = message.text.strip().split(" ", 1)
    try:
        search_query = args[1]
    except:
        update.effective_message.reply_text("Format : /manga <manganame>")
        return

    progress_message = update.effective_message.reply_text("Searching.... ")
    jikan = jikanpy.jikan.Jikan()
    
    search_result = jikan.search("manga", search_query)
    first_mal_id = search_result["results"][0]["mal_id"]
    
    manga = jikan.manga(first_mal_id)

    caption = f"[ ]({manga['image_url']})[{manga['title']}]({manga['url']})"

    if manga['title_japanese']:
        caption += f" ({manga['title_japanese']})\n"
    else:
        caption += "\n"

    alternative_names = [manga['title_english']]
    alternative_names.extend(manga['title_synonyms'])

    if alternative_names and None not in alternative_names:
        alternative_names_string = ", ".join(alternative_names)
        caption += f"\n*Alternative Names* : `{alternative_names_string}`"

    genre_string = ', '.join([genre_info['name'] for genre_info in manga['genres']])
    synopsis = manga['synopsis'].split(" ", 60)

    try:
        synopsis.pop(60)
    except IndexError:
        pass

    synopsis_string = ' '.join(synopsis)

    caption += textwrap.dedent(f"""
    *Type*: `{manga['type']}`
    *Status*: `{manga['status']}`
    *Volumes*: `{manga['volumes']}`
    *Chapters*: `{manga['chapters']}`
    *Genres*: `{genre_string}`

    📖 *Synopsis*: {synopsis_string}...
    """)

    buttons = [
        [InlineKeyboardButton(info_btn, url=manga['url'])]
    ]

    progress_message.delete()
    update.effective_message.reply_text(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=False)

@run_async
def character(bot: Bot, update: Update):

    message = update.effective_message
    args = message.text.strip().split(" ", 1)
    try:
        search_query = args[1]
    except:
        update.effective_message.reply_text("Format : /character <charactername>")
        return

    progress_message = update.effective_message.reply_text("Searching.... ")
    jikan = jikanpy.jikan.Jikan()
    
    search_result = jikan.search("character", search_query)
    first_mal_id = search_result["results"][0]["mal_id"]
    
    character = jikan.character(first_mal_id)

    caption = f"[ ]({character['image_url']})[{character['name']}]({character['url']})"

    if character['name_kanji'] != "Japanese":
        caption += f" ({character['name_kanji']})\n"
    else:
        caption += "\n"

    if character['nicknames']:
        nicknames_string = ", ".join(character['nicknames'])
        caption += f"\n*Nicknames* : `{nicknames_string}`"

    about = character['about'].split(" ", 60)

    try:
        about.pop(60)
    except IndexError:
        pass

    about_string = ' '.join(about)

    caption += f"\n*About*: {about_string}..."

    buttons = [
        [InlineKeyboardButton(info_btn, url=character['url'])]
    ]

    progress_message.delete()
    update.effective_message.reply_text(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=False)

@run_async
def user(bot: Bot, update: Update):

    message = update.effective_message
    args = message.text.strip().split(" ", 1)
    try:
        search_query = args[1]
    except:
        update.effective_message.reply_text("Format : /user <username>")
        return

    jikan = jikanpy.jikan.Jikan()
    
    try:
        user = jikan.user(search_query)
    except jikanpy.APIException:
        update.effective_message.reply_text("Username not found.")
        return

    progress_message = update.effective_message.reply_text("Searching.... ")

    date_format = "%Y-%m-%d"

    try:
        user_birthday = datetime.datetime.fromisoformat(user['birthday'])
        user_birthday_formatted = user_birthday.strftime(date_format)
    except:
        user_birthday_formatted = "No info"

    user_joined_date = datetime.datetime.fromisoformat(user['joined'])
    user_joined_date_formatted = user_joined_date.strftime(date_format)

    for entity in user:
        if user[entity] == None:
            user[entity] = "No info"
    
    about = user['about'].split(" ", 60)

    try:
        about.pop(60)
    except IndexError:
        pass

    about_string = ' '.join(about)
    about_string = about_string.replace("<br>", "").strip().replace("\r\n", "\n")
    
    #caption = f"[ ]({user['image_url']})" #coz jikan user img is currently broken
    caption = ""

    caption += textwrap.dedent(f"""
    *Username*: [{user['username']}]({user['url']})

    *Gender*: `{user['gender']}`
    *Birthday*: `{user_birthday_formatted}`
    *Joined*: `{user_joined_date_formatted}`
    *Days wasted watching anime*: `{user['anime_stats']['days_watched']}`
    *Days wasted reading manga*: `{user['manga_stats']['days_read']}`

    """)

    caption += f"*About*: {about_string}..."

    buttons = [
        [InlineKeyboardButton(info_btn, url=user['url'])]
    ]

    progress_message.delete()
    update.effective_message.reply_text(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(buttons), disable_web_page_preview=False)
    
@run_async
def upcoming(bot: Bot, update: Update):

    jikan = jikanpy.jikan.Jikan()
    upcoming = jikan.top('anime', page=1, subtype="upcoming")

    upcoming_list = [entry['title'] for entry in upcoming['top']]
    upcoming_message = ""

    for entry_num in range(len(upcoming_list)):
        if entry_num == 10:
            break
        upcoming_message += f"{entry_num + 1}. {upcoming_list[entry_num]}\n"
        
    update.effective_message.reply_text(upcoming_message)

__help__ = """
Get information about anime, manga or characters from [MyAnimeList](https://myanimelist.net).

*Available commands:*

 - /anime <anime>: returns information about the anime.

 - /character <character>: returns information about the character.

 - /manga <manga>: returns information about the manga.

 - /user <user>: returns information about a MyAnimeList user.

 - /upcoming: returns a list of new anime in the upcoming seasons.

 """

__mod_name__ = "MyAnimeList"

ANIME_HANDLER = CommandHandler("anime", anime)
CHARACTER_HANDLER = CommandHandler("character", character)
MANGA_HANDLER = CommandHandler("manga", manga)
USER_HANDLER = CommandHandler("user", user)
UPCOMING_HANDLER = CommandHandler("upcoming", upcoming)

dispatcher.add_handler(ANIME_HANDLER)
dispatcher.add_handler(CHARACTER_HANDLER)
dispatcher.add_handler(MANGA_HANDLER)
dispatcher.add_handler(USER_HANDLER)
dispatcher.add_handler(UPCOMING_HANDLER)