import re

def analyze():
    with open('insta_dump.html', encoding='utf-8') as f:
        html = f.read()
    
    print("Login string found:", 'Login' in html and 'Instagram' in html)
    print("RequireLazy found:", bool(re.search(r'requireLazy', html)))
    print("Meta tags:", re.findall(r'<meta property="og:description" content="([^"]+)"', html))
    print("Title:", re.findall(r'<title>([^<]+)</title>', html))
    
    # Try to find JSON chunks
    json_chunks = re.findall(r'<script type="application/json"[^>]*>(.*?)</script>', html)
    print(f"Found {len(json_chunks)} JSON chunks")
    for i, chunk in enumerate(json_chunks[:3]):
        print(f"Chunk {i} size: {len(chunk)} preview: {chunk[:100]}")

if __name__ == '__main__':
    analyze()
