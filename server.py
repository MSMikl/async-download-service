import aiofiles
import asyncio
import logging
import os

from aiohttp import web
from environs import Env


env = Env()

logger = logging.getLogger('server')


async def handle_index_page(request):
    async with aiofiles.open('index.html', mode='r') as index_file:
        index_contents = await index_file.read()
    return web.Response(text=index_contents, content_type='text/html')


async def send_archive(request):
    photo_dir = request.match_info['archive_hash']
    photo_path = env('PHOTO_PATH', 'test_photos')
    path = os.path.join(photo_path, photo_dir)
    if not os.path.isdir(path):
        raise web.HTTPNotFound(text='Архива не существует, или он был удален')
    args = ['-r', '-9', '-', '.']
    response = web.StreamResponse()
    response.headers['Content-Type'] = 'multipart/form-data'
    response.headers['Content-Disposition'] = "attachment; filename=photos.zip"
    await response.prepare(request)
    process = await asyncio.create_subprocess_exec('zip', *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, cwd=path)
    number = 0
    delay = env.int('DELAY', 0)
    try:
        while not process.stdout.at_eof():
            part = await process.stdout.read(500000)
            if delay:
                await asyncio.sleep(delay)
            number += 1
            logger.info(f"Sending archive chunk {number}")
            await response.write(part)
    except ConnectionResetError:
        logger.warning('Downloading cancelled')
        await process.communicate()
        return
    except asyncio.CancelledError:
        logger.exception()
        await process.communicate()
        raise
    except:
        logger.exception()
        await process.communicate()
        return
    await process.communicate()
    if process.returncode == 0: 
        return response


if __name__ == '__main__':
    env.read_env()
    logging_turned_on = env.bool('LOGGING', True)
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.INFO)
    logger.setLevel(logging.INFO)
    if logging_turned_on:
        logger.addHandler(stream_handler)
    app = web.Application()
    app.add_routes([
        web.get('/', handle_index_page),
        web.get('/archive/{archive_hash}/', send_archive),
    ])
    web.run_app(app)
