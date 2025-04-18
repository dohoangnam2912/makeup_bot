export default function Footer() {
    return (
      <footer className="bg-gray-100 text-center text-sm text-gray-600 py-4 mt-10">
        © {new Date().getFullYear()} RAG Assistant · Powered by FastAPI + React
      </footer>
    );
  }