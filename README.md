# Armoseal Insulation website

A redesign of armosealinsulation.com, built as a plain static site using HTML, CSS and a little JavaScript. It has no build step, so it can go on any web host as-is.

## Pages
- `index.html`: Home
- `services.html`: Spray foam, fiberglass, home inspection
- `about.html`: Mission and values
- `contact.html`: Phone, email, address, quote form

## View it on your computer
```bash
python3 -m http.server 8080
```
Then open http://localhost:8080. You can also double-click `index.html`.

## Things to fill in
- To find every spot that still needs your details, search for `class="todo"` (yellow highlighted boxes): hours, service area, company story.
- Photos: the striped boxes marked with a dashed border are placeholders. Put your photos in `images/` and replace each `photo-placeholder` block with `<div class="photo"><img src="images/your-photo.jpg" alt="Short description"></div>`.
- Testimonials: there is a ready-to-use block, commented out, in `index.html`. Fill it in with real customer reviews.
- Service descriptions on the Services page are plain-language explanations. Check that they match how you work.

## Putting it online later
Upload this whole folder to any static host. Netlify, Cloudflare Pages and GitHub Pages are all free. Then connect your domain. The quote form currently opens the visitor's email app. Once the site is online, you can switch it to a form service such as Formspree or Netlify Forms so requests come straight to your inbox.
