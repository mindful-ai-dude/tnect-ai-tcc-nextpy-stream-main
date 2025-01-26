# AI SDK Python Streaming Preview

This template demonstrates the usage of [Data Stream Protocol](https://sdk.vercel.ai/docs/ai-sdk-ui/stream-protocol#data-stream-protocol) to stream chat completions from a Python endpoint ([FastAPI](https://fastapi.tiangolo.com)) and display them using the [useChat](https://sdk.vercel.ai/docs/ai-sdk-ui/chatbot#chatbot) hook in your Next.js application.

## Deploy your own

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https%3A%2F%2Fgithub.com%2Fvercel-labs%2Fai-sdk-preview-python-streaming&env=OPENAI_API_KEY&envDescription=API%20keys%20needed%20for%20application&envLink=https%3A%2F%2Fgithub.com%2Fvercel-labs%2Fai-sdk-preview-python-streaming%2Fblob%2Fmain%2F.env.example)

## How to use

Run [`create-next-app`](https://github.com/vercel/next.js/tree/canary/packages/create-next-app) with [npm](https://docs.npmjs.com/cli/init), [Yarn](https://yarnpkg.com/lang/en/docs/cli/create/), or [pnpm](https://pnpm.io) to bootstrap the example:

```bash
npx create-next-app --example https://github.com/vercel-labs/ai-sdk-preview-python-streaming ai-sdk-preview-python-streaming-example
```

```bash
yarn create next-app --example https://github.com/vercel-labs/ai-sdk-preview-python-streaming ai-sdk-preview-python-streaming-example
```

```bash
pnpm create next-app --example https://github.com/vercel-labs/ai-sdk-preview-python-streaming ai-sdk-preview-python-streaming-example
```

1. Sign up for accounts with the AI providers you want to use (e.g., Gemini).
2. Obtain API keys for each provider.
3. Set the required environment variables as shown in the `.env.example` file, but in a new file called `.env`.
4. `pnpm install` to install the required Node dependencies.
5. `conda create --name myenv python=3.12` to create a Conda virtual environment.
6. `conda activate myenv` to activate the virtual environment.
7. `pip install -r requirements.txt` to install the required Python dependencies.
8. `pnpm dev` to launch the development server.

### 1. Explanation of the Script in `package.json`

```json
"fastapi-dev": "pip3 install -r requirements.txt && python3 -m uvicorn api.index:app --reload"
```

#### Breakdown:
- **`pip3 install -r requirements.txt`**: This command uses `pip3`, the package installer for Python, to install all the dependencies listed in the `requirements.txt` file. This file typically contains a list of Python packages that your FastAPI application needs to run.

- **`&&`**: This operator allows you to run multiple commands in sequence. The second command will only run if the first command is successful (i.e., it completes without errors).

- **`python3 -m uvicorn api.index:app --reload`**: This command starts the FastAPI application using Uvicorn, an ASGI server. 
  - `api.index:app` specifies the location of your FastAPI application instance. It means that in the `api/index.py` file, there should be an `app` object that is your FastAPI application.
  - `--reload` enables auto-reloading, which means the server will automatically restart whenever you make changes to your code. This is useful during development.

#### macOS-Check python version:

```bash
python3 --version
pip3 --version
```

### 2. Running `pnpm` and Installing Dependencies

When you run `pnpm`, it installs the dependencies listed in your `package.json` file, not the `requirements.txt` file. 

#### Why It Didn't Install Python Dependencies:
- **`pnpm`** is a package manager for JavaScript/Node.js projects, and it does not manage Python packages. Therefore, it will not read or install anything from `requirements.txt`.
- To install Python dependencies, you need to run the `fastapi-dev` script you mentioned earlier, which uses `pip3`.

### Summary of Steps
1. To install your JavaScript dependencies, run:
   ```bash
   pnpm install
   ```

2. To install your Python dependencies, run:
   ```bash
   npm run fastapi-dev
   ```

This will ensure that both your Node.js and Python dependencies are installed correctly. If you have any further questions or need additional assistance, feel free to ask!


