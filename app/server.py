import aiohttp
import asyncio
import uvicorn
from fastai import *
from fastai.vision import *
from io import BytesIO
from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse, JSONResponse
from starlette.staticfiles import StaticFiles

# export_file_url = 'https://drive.google.com/uc?export=download&id=1o3wmeFwBXp88ZBtfUYK8nAyVOAWqDF5c'
# export_file_name = 'resnet50(91).pkl'
# classes = ['hentai', 'kiss', 'neutral', 'sexy', 'porn']

export_file_url = 'https://drive.google.com/uc?export=download&id=1WPzZ_MAs8SDhCd5DSuG8tWlumjOFwrmL'
export_file_name = 'resnet34(89%_4class).pkl'
classes = ['kiss', 'neutral', 'porn', 'sexy']

path = Path(__file__).parent

app = Starlette()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_headers=['X-Requested-With', 'Content-Type'])
app.mount('/static', StaticFiles(directory='app/static'))


async def download_file(url, dest):
    if dest.exists(): return
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.read()
            with open(dest, 'wb') as f:
                f.write(data)


async def setup_learner():
    await download_file(export_file_url, path / export_file_name)
    try:
        learn = load_learner(path, export_file_name)
        return learn
    except RuntimeError as e:
        if len(e.args) > 0 and 'CPU-only machine' in e.args[0]:
            print(e)
            message = "\n\nThis model was trained with an old version of fastai and will not work in a CPU environment.\n\nPlease update the fastai library in your training environment and export your model again.\n\nSee instructions for 'Returning to work' at https://course.fast.ai."
            raise RuntimeError(message)
        else:
            raise


loop = asyncio.get_event_loop()
tasks = [asyncio.ensure_future(setup_learner())]
learn = loop.run_until_complete(asyncio.gather(*tasks))[0]
loop.close()


@app.route('/')
async def homepage(request):
    html_file = path / 'view' / 'index.html'
    return HTMLResponse(html_file.open().read())


# def predict_single(img_file):
#     'function to take image and return prediction'
#     prediction = learn.predict(open_image(img_file))
#     probs_list = prediction[2].numpy()
#     return {
#         'category': classes[prediction[1].item()],
#         'probs': {c: round(float(probs_list[i]), 5) for (i, c) in enumerate(classes)}
#     }


# @app.route('/analyze', methods=['POST'])
# async def analyze(request):
#     img_data = await request.form()
#     img_bytes = await (img_data['file'].read())
#     img = open_image(BytesIO(img_bytes))
#     prediction = learn.predict(img)
#     probs_list = prediction[2].numpy()
#     return JSONResponse({
#         'category': classes[prediction[1].item()],
#         'probs': {c: round(float(probs_list[i]), 5) for (i, c) in enumerate(classes)}
#     })

@app.route('/analyze', methods=['POST'])
async def analyze(request):
    img_data = await request.form()
    img_bytes = await (img_data['file'].read())
    img = open_image(BytesIO(img_bytes))
    
    pred_1_class, indice, preds = learn.predict(img)
    preds_sorted, idxs = preds.sort(descending=True)
    
    pred_2_class = learn.data.classes[idxs[1]]
    pred_3_class = learn.data.classes[idxs[2]]
    pred_4_class = learn.data.classes[idxs[3]]
#     pred_5_class = learn.data.classes[idxs[4]]
    
    # Get best 3 predictions - probabilities
    pred_1_prob = np.round(100*preds_sorted[0].item(),2)
    pred_2_prob = np.round(100*preds_sorted[1].item(),2)
    pred_3_prob = np.round(100*preds_sorted[2].item(),2)
    pred_4_prob = np.round(100*preds_sorted[3].item(),2)
#     pred_5_prob = np.round(100*preds_sorted[4].item(),2)
    
    preds_All = [f'{pred_1_class} ({pred_1_prob}%)', 
                   f'{pred_2_class} ({pred_2_prob}%)', 
                   f'{pred_3_class} ({pred_3_prob}%)',
                   f'{pred_4_class} ({pred_4_prob}%)']
#                  f'{pred_5_class} ({pred_5_prob}%)']
    
    return JSONResponse({'result': str(preds_All)})



# @app.route('/analyze', methods=['POST'])
# async def analyze(request):
#     img_data = await request.form()
#     img_bytes = await (img_data['file'].read())
#     img = open_image(BytesIO(img_bytes))
#     prediction = learn.predict(img)[0]
#     return JSONResponse({'result': str(prediction)})


if __name__ == '__main__':
    if 'serve' in sys.argv:
        uvicorn.run(app=app, host='0.0.0.0', port=5000, log_level="info")
