#!/usr/bin/env python3
import asyncio
import click
from playwright.async_api import async_playwright
import os

async def debug_images(page):
    """Debug image loading status"""
    image_info = await page.evaluate("""
        () => {
            const images = Array.from(document.querySelectorAll('.rich_media_content img'));
            return images.map(img => ({
                src: img.src,
                dataSrc: img.dataset.src,
                complete: img.complete,
                naturalWidth: img.naturalWidth,
                naturalHeight: img.naturalHeight,
                offsetTop: img.offsetTop
            }));
        }
    """)
    print("\nImage Debug Information:")
    for idx, img in enumerate(image_info, 1):
        print(f"Image {idx}:")
        print(f"  Complete: {img['complete']}")
        print(f"  Natural Size: {img['naturalWidth']}x{img['naturalHeight']}")
        print(f"  Position: {img['offsetTop']}px from top")
        print(f"  Src: {img['src']}")
        print(f"  Data-Src: {img.get('dataSrc', 'None')}")
        print()

async def wait_for_images(page, timeout_ms=30000):
    """
    Wait for images to load on the page
    Returns the number of images found
    """
    try:
        # Count all images in the article
        image_count = await page.evaluate("""
            () => {
                const images = document.querySelectorAll('.rich_media_content img');
                return images.length;
            }
        """)
        
        if image_count > 0:
            print(f"Found {image_count} images, waiting for them to load...")
            
            try:
                # Wait for all images to have either loaded or failed
                await asyncio.wait_for(
                    page.evaluate("""
                        () => {
                            const images = Array.from(document.querySelectorAll('.rich_media_content img'));
                            return Promise.all(images.map(img => {
                                if (img.complete) return Promise.resolve();
                                return new Promise((resolve, reject) => {
                                    img.addEventListener('load', resolve);
                                    img.addEventListener('error', resolve); // Resolve on error too to avoid hanging
                                });
                            }));
                        }
                    """),
                    timeout=timeout_ms/1000  # Convert to seconds for asyncio.wait_for
                )
            except asyncio.TimeoutError:
                print("Image loading timed out, continuing anyway...")
            
            print("Image loading completed")
            # Debug image status
            await debug_images(page)
        return image_count
    except Exception as e:
        print(f"Warning: Error while waiting for images: {str(e)}")
        return 0

async def capture_webpage(url: str, output: str, width: int = 414, height: int = 896):
    """
    Capture a webpage and convert it to PDF using Playwright
    """
    async with async_playwright() as p:
        # Launch the browser with slower network to ensure better image loading
        browser = await p.chromium.launch()
        
        try:
            # Create a new page with mobile viewport for WeChat articles
            context = await browser.new_context(
                viewport={'width': width, 'height': height},
                user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
            )
            page = await context.new_page()
            
            # Set longer timeout for navigation
            page.set_default_timeout(60000)
            
            # Navigate to the URL with longer timeout for WeChat
            print("Loading page...")
            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # Wait for article content to load
            print("Waiting for article content...")
            await page.wait_for_selector('.rich_media_content', timeout=10000)
            
            # First scroll to activate all lazy loading
            print("Scrolling through page to trigger lazy loading...")
            await page.evaluate("""
                () => {
                    return new Promise((resolve) => {
                        let totalHeight = 0;
                        const distance = 100;
                        const timer = setInterval(() => {
                            const scrollHeight = document.body.scrollHeight;
                            window.scrollBy(0, distance);
                            totalHeight += distance;
                            
                            if(totalHeight >= scrollHeight){
                                clearInterval(timer);
                                window.scrollTo(0, 0);  // Scroll back to top
                                resolve();
                            }
                        }, 100);
                    });
                }
            """)
            
            # Wait for initial scroll to complete
            await page.wait_for_timeout(2000)
            
            # Enhanced image loading with retries
            print("Ensuring all images are loaded...")
            await page.evaluate("""
                () => {
                    return new Promise((resolve) => {
                        const loadImage = (img) => {
                            return new Promise((resolveImg) => {
                                if (img.complete && img.naturalWidth > 1) {
                                    resolveImg();
                                    return;
                                }
                                
                                const originalSrc = img.src;
                                if (img.dataset.src) {
                                    img.src = img.dataset.src;
                                }
                                
                                img.onload = () => resolveImg();
                                img.onerror = () => {
                                    // On error, try to reload original source
                                    if (originalSrc !== img.src) {
                                        img.src = originalSrc;
                                    }
                                    resolveImg();
                                };
                            });
                        };
                        
                        const images = Array.from(document.querySelectorAll('.rich_media_content img'));
                        Promise.all(images.map(img => loadImage(img))).then(resolve);
                    });
                }
            """)
            
            # Wait for images to settle
            await page.wait_for_timeout(5000)
            
            # Final check of images
            print("Performing final image check...")
            await debug_images(page)
            
            # Ensure all images are visible in viewport
            await page.evaluate("""
                () => {
                    const images = document.querySelectorAll('.rich_media_content img');
                    images.forEach(img => {
                        img.scrollIntoView();
                    });
                }
            """)
            
            # Wait a bit more for any final image loading
            await page.wait_for_timeout(5000)
            
            # Ensure the output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)
            
            # Generate PDF with better settings for articles
            print("Generating PDF...")
            await page.pdf(
                path=output,
                format="A4",
                print_background=True,
                margin={
                    'top': '20px',
                    'right': '20px',
                    'bottom': '20px',
                    'left': '20px'
                }
            )
            
            print(f"Successfully created PDF: {output}")
            
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            raise e
        
        finally:
            await browser.close()

@click.command()
@click.option('--url', required=True, help='Target webpage URL')
@click.option('--output', required=True, help='Output PDF file path')
@click.option('--width', default=414, help='Viewport width (default: 414 for mobile view)')
@click.option('--height', default=896, help='Viewport height (default: 896 for mobile view)')
def main(url: str, output: str, width: int, height: int):
    """Convert webpage to PDF using headless browser"""
    asyncio.run(capture_webpage(url, output, width, height))

if __name__ == '__main__':
    main()
