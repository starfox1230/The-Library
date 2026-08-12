(() => {
  'use strict';

  const CURRENT_STORY_ID = 'slowly-slowly-dinosaur-valley';

  // Add future stories here. Each story can point to another reader page and
  // provide its own groups of educational Google Images lookups.
  const STORY_LIBRARY = [
    {
      id: CURRENT_STORY_ID,
      title: 'PAW Patrol and the Slowly, Slowly Dinosaur Valley',
      shortTitle: 'Slowly, Slowly Dinosaur Valley',
      summary: 'A quiet bedtime mission through dinosaur families, prehistoric adaptations, and the branches of the dinosaur family tree.',
      href: './index.html',
      imageGroups: [
        {
          title: 'The pups’ prehistoric forms',
          items: [
            ['Skye → Pteranodon', 'A flying reptile—not a dinosaur', 'Pteranodon paleontology life reconstruction'],
            ['Chase → Utahraptor', 'A large, feathered dromaeosaur', 'Utahraptor feathered life reconstruction paleontology'],
            ['Marshall → Carnotaurus', 'Brow horns and remarkably tiny arms', 'Carnotaurus life reconstruction paleontology'],
            ['Rubble → Ankylosaurus', 'Bony armor and a tail club', 'Ankylosaurus life reconstruction paleontology'],
            ['Rocky → Stegosaurus', 'Back plates and tail spikes', 'Stegosaurus life reconstruction paleontology'],
            ['Zuma → Spinosaurus', 'A long snout and tall back sail', 'Spinosaurus life reconstruction paleontology'],
            ['Everest → Pachyrhinosaurus', 'A ceratopsian with a broad nasal boss', 'Pachyrhinosaurus life reconstruction paleontology'],
            ['Liberty → Protoceratops', 'A small, sturdy ceratopsian', 'Protoceratops life reconstruction paleontology'],
            ['Tracker → Parasaurolophus', 'A hollow-crested hadrosaur', 'Parasaurolophus life reconstruction paleontology'],
            ['Rex → Tyrannosaurus rex', 'A giant tyrannosaurid theropod', 'Tyrannosaurus rex accurate life reconstruction paleontology'],
          ],
        },
        {
          title: 'Other animals named in the story',
          items: [
            ['Albertosaurus', 'A slender North American tyrannosaurid', 'Albertosaurus life reconstruction paleontology'],
            ['Brachiosaurus', 'A high-shouldered sauropod', 'Brachiosaurus life reconstruction paleontology'],
            ['Corythosaurus', 'A helmet-crested hadrosaur', 'Corythosaurus life reconstruction paleontology'],
            ['Diplodocus', 'A long-tailed sauropod', 'Diplodocus life reconstruction paleontology'],
            ['Edmontosaurus', 'A broad-billed hadrosaur', 'Edmontosaurus life reconstruction paleontology'],
            ['Gorgosaurus', 'A close tyrannosaurid relative', 'Gorgosaurus life reconstruction paleontology'],
            ['Styracosaurus', 'A ceratopsian with long frill spikes', 'Styracosaurus life reconstruction paleontology'],
            ['Triceratops', 'Three horns and a solid frill', 'Triceratops life reconstruction paleontology'],
            ['Velociraptor', 'A small feathered dromaeosaur', 'Velociraptor feathered life reconstruction paleontology'],
          ],
        },
        {
          title: 'See the science',
          items: [
            ['Ceratopsian skulls', 'Compare horns, frills, and nasal bosses', 'ceratopsian skull comparison Triceratops Styracosaurus Pachyrhinosaurus Protoceratops'],
            ['Armored dinosaurs', 'Ankylosaur armor compared with stegosaur plates', 'ankylosaur stegosaur armor comparison diagram'],
            ['Hadrosaur crests', 'How hollow crests may have shaped sound', 'Parasaurolophus Corythosaurus hollow crest anatomy diagram'],
            ['Spinosaur adaptations', 'Long jaws, sail, and water-linked anatomy', 'Spinosaurus adaptations anatomy diagram paleontology'],
            ['Feathered raptors', 'Evidence for feathers in dromaeosaurs', 'dromaeosaur feather fossil reconstruction diagram'],
            ['Abelisaurid arms', 'Carnotaurus and its reduced forelimbs', 'Carnotaurus abelisaurid forelimb anatomy'],
            ['Tyrannosaur family', 'Compare T. rex, Albertosaurus, and Gorgosaurus', 'tyrannosauridae family comparison Tyrannosaurus Albertosaurus Gorgosaurus'],
            ['Sauropod shapes', 'Compare Brachiosaurus and Diplodocus', 'Brachiosaurus Diplodocus body shape comparison'],
            ['Pterosaur wings', 'A skin-and-muscle wing built around one long finger', 'Pteranodon pterosaur wing anatomy diagram'],
            ['Birds are dinosaurs', 'See birds inside the dinosaur family tree', 'birds are dinosaurs evolutionary family tree diagram'],
          ],
        },
      ],
    },
  ];

  const drawer = document.querySelector('#drawer');
  const drawerHead = drawer && drawer.querySelector('.drawer-head');
  const drawerContent = drawer && drawer.querySelector('.drawer-links');
  const closeButton = document.querySelector('#close');
  const menuButton = document.querySelector('#menu');
  const scrim = document.querySelector('#scrim');

  if (!drawer || !drawerHead || !drawerContent || !closeButton) return;

  const currentStory = STORY_LIBRARY.find((story) => story.id === CURRENT_STORY_ID);
  const chapters = [...document.querySelectorAll('.reader h2[id]')].map((heading, index) => ({
    id: heading.id,
    title: heading.textContent.trim(),
    number: index + 1,
  }));
  const imageCount = currentStory.imageGroups.reduce((total, group) => total + group.items.length, 0);

  function escapeHtml(value) {
    return String(value)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function closeDrawer() {
    drawer.classList.remove('open');
    scrim && scrim.classList.remove('open');
    menuButton && menuButton.focus();
  }

  drawer.setAttribute('aria-label', 'Story library');
  if (menuButton) menuButton.setAttribute('aria-label', 'Open story library');
  closeButton.setAttribute('aria-label', 'Close story library');

  drawerHead.innerHTML =
    '<div class="drawer-title-wrap">' +
      '<span class="drawer-kicker">Educational story library</span>' +
      '<span class="drawer-title">' + escapeHtml(currentStory.shortTitle) + '</span>' +
    '</div>' +
    '<button id="close" aria-label="Close story library">×</button>';

  const replacementCloseButton = drawerHead.querySelector('#close');
  replacementCloseButton.addEventListener('click', closeDrawer);

  const tabs = document.createElement('div');
  tabs.className = 'drawer-tabs';
  tabs.setAttribute('role', 'tablist');
  tabs.setAttribute('aria-label', 'Browse the story library');
  tabs.innerHTML = [
    ['stories', 'Stories', STORY_LIBRARY.length],
    ['chapters', 'Chapters', chapters.length],
    ['images', 'Images', imageCount],
  ].map(([id, label, count]) =>
    '<button class="drawer-tab" id="tab-' + id + '" role="tab" aria-controls="panel-' + id + '" aria-selected="' + (id === 'chapters') + '" tabindex="' + (id === 'chapters' ? '0' : '-1') + '">' +
      label + '<span class="drawer-tab-count">' + count + '</span>' +
    '</button>'
  ).join('');

  drawerHead.insertAdjacentElement('afterend', tabs);
  drawerContent.setAttribute('aria-live', 'polite');

  function renderStories() {
    drawerContent.innerHTML =
      '<section class="drawer-panel" id="panel-stories" role="tabpanel" aria-labelledby="tab-stories">' +
        '<p class="panel-intro">Choose a story. New educational adventures will appear here as the library grows.</p>' +
        STORY_LIBRARY.map((story) => {
          const isCurrent = story.id === CURRENT_STORY_ID;
          return '<a class="story-card" href="' + escapeHtml(story.href) + '"' + (isCurrent ? ' data-current-story="true"' : '') + '>' +
            '<span class="story-card-title">' + escapeHtml(story.title) + '</span>' +
            '<span class="story-card-summary">' + escapeHtml(story.summary) + '</span>' +
            '<span class="story-card-meta"><span>' + (isCurrent ? chapters.length + ' chapters' : 'Open story') + '</span>' +
            (isCurrent ? '<span class="reading-badge">Reading now</span>' : '') + '</span>' +
          '</a>';
        }).join('') +
      '</section>';

    const currentLink = drawerContent.querySelector('[data-current-story="true"]');
    if (currentLink) {
      currentLink.addEventListener('click', (event) => {
        event.preventDefault();
        closeDrawer();
        window.scrollTo({ top: 0, behavior: 'smooth' });
      });
    }
  }

  function renderChapters() {
    drawerContent.innerHTML =
      '<section class="drawer-panel" id="panel-chapters" role="tabpanel" aria-labelledby="tab-chapters">' +
        '<p class="panel-intro">Jump to any chapter in “' + escapeHtml(currentStory.shortTitle) + '.”</p>' +
        '<div class="chapter-list">' +
          chapters.map((chapter) =>
            '<a class="chapter-link" href="#' + escapeHtml(chapter.id) + '">' +
              '<span class="chapter-number">' + String(chapter.number).padStart(2, '0') + '</span>' +
              '<span>' + escapeHtml(chapter.title) + '</span>' +
            '</a>'
          ).join('') +
        '</div>' +
      '</section>';

    drawerContent.querySelectorAll('.chapter-link').forEach((link) => {
      link.addEventListener('click', () => window.setTimeout(closeDrawer, 80));
    });
  }

  function googleImagesUrl(query) {
    return 'https://www.google.com/search?tbm=isch&q=' + encodeURIComponent(query);
  }

  function imageItemMarkup(item) {
    const [title, note, query] = item;
    return '<a class="image-link" href="' + googleImagesUrl(query) + '" target="_blank" rel="noopener noreferrer" data-image-terms="' + escapeHtml((title + ' ' + note).toLowerCase()) + '">' +
      '<span class="image-link-copy">' +
        '<span class="image-link-title">' + escapeHtml(title) + '</span>' +
        '<span class="image-link-note">' + escapeHtml(note) + '</span>' +
      '</span>' +
      '<span class="image-link-icon" aria-hidden="true">↗</span>' +
    '</a>';
  }

  function renderImages() {
    drawerContent.innerHTML =
      '<section class="drawer-panel" id="panel-images" role="tabpanel" aria-labelledby="tab-images">' +
        '<p class="panel-intro">Open a Google Images search for every prehistoric animal and visual science idea in this story.</p>' +
        '<div class="image-search"><label for="image-filter">Find an image topic</label><input id="image-filter" type="search" placeholder="Find a dinosaur or science idea…" autocomplete="off"></div>' +
        currentStory.imageGroups.map((group) =>
          '<section class="image-group">' +
            '<h3 class="image-group-title">' + escapeHtml(group.title) + '</h3>' +
            '<div class="image-list">' + group.items.map(imageItemMarkup).join('') + '</div>' +
          '</section>'
        ).join('') +
        '<div class="empty-images" hidden>No matching picture links. Try another word.</div>' +
      '</section>';

    const filter = drawerContent.querySelector('#image-filter');
    const empty = drawerContent.querySelector('.empty-images');
    filter.addEventListener('input', () => {
      const term = filter.value.trim().toLowerCase();
      let visibleCount = 0;
      drawerContent.querySelectorAll('.image-link').forEach((link) => {
        const visible = !term || link.dataset.imageTerms.includes(term);
        link.hidden = !visible;
        if (visible) visibleCount += 1;
      });
      drawerContent.querySelectorAll('.image-group').forEach((group) => {
        group.hidden = !group.querySelector('.image-link:not([hidden])');
      });
      empty.hidden = visibleCount > 0;
    });
  }

  const renderers = {
    stories: renderStories,
    chapters: renderChapters,
    images: renderImages,
  };

  function selectTab(id, focus = false) {
    tabs.querySelectorAll('[role="tab"]').forEach((tab) => {
      const selected = tab.id === 'tab-' + id;
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected ? 0 : -1;
      if (selected && focus) tab.focus();
    });
    renderers[id]();
  }

  tabs.addEventListener('click', (event) => {
    const tab = event.target.closest('[role="tab"]');
    if (tab) selectTab(tab.id.replace('tab-', ''));
  });

  tabs.addEventListener('keydown', (event) => {
    if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
    const allTabs = [...tabs.querySelectorAll('[role="tab"]')];
    const currentIndex = allTabs.indexOf(document.activeElement);
    let nextIndex = currentIndex;
    if (event.key === 'ArrowLeft') nextIndex = (currentIndex - 1 + allTabs.length) % allTabs.length;
    if (event.key === 'ArrowRight') nextIndex = (currentIndex + 1) % allTabs.length;
    if (event.key === 'Home') nextIndex = 0;
    if (event.key === 'End') nextIndex = allTabs.length - 1;
    event.preventDefault();
    selectTab(allTabs[nextIndex].id.replace('tab-', ''), true);
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && drawer.classList.contains('open')) closeDrawer();
  });

  renderChapters();
})();
