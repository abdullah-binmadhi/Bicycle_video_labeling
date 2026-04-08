import re

with open('desktop-app/src/index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Inject Training Graph Dropdown
train_header_old = r'''  <!-- Charts Row -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">'''

train_header_new = '''  <!-- Charts Row Header & Filter -->
  <div class="flex justify-between items-end mb-4">
      <h2 class="text-sm uppercase tracking-widest font-bold text-gray-300">Model Performance Metrics</h2>
      <div class="relative group">
          <button class="bg-[#1a1a1a] border border-[#333] px-3 py-1 text-xs text-gray-300 hover:text-white rounded flex items-center gap-2">
              <i class="fa-solid fa-filter"></i> Filter Classes
          </button>
          <div class="absolute right-0 top-full mt-1 w-64 bg-[#111] border border-[#333] shadow-lg hidden group-hover:flex flex-col z-50 max-h-64 overflow-y-auto p-2" id="training-filter-dropdown">
              <!-- Dynamically populated -->
          </div>
      </div>
  </div>
  
  <!-- Charts Row -->
  <div class="grid grid-cols-1 lg:grid-cols-2 gap-6 w-full">'''

content = re.sub(train_header_old, train_header_new, content)

# 2. Inject Distance Graph Dropdown
dist_header_old = r'''           <h3 class="text-cyan-400 font-medium tracking-widest text-xs uppercase self-start mb-4 w-full border-b border-\[#333\] pb-2">Total Distance per Surface \(m\)</h3>
           <div class="w-full h-full relative h-\[250px\]">'''

dist_header_new = '''           <div class="w-full flex justify-between items-center border-b border-[#333] pb-2 mb-4">
               <h3 class="text-cyan-400 font-medium tracking-widest text-xs uppercase self-start">Total Distance per Surface (m)</h3>
               <div class="relative group">
                 <button class="text-xs text-gray-400 hover:text-white flex items-center gap-1"><i class="fa-solid fa-filter"></i> Filter</button>
                 <div class="absolute right-0 top-full mt-2 w-48 bg-[#111] border border-[#333] max-h-48 overflow-y-auto hidden group-hover:flex flex-col z-50 shadow-xl p-2" id="distance-filter-dropdown">
                 </div>
               </div>
           </div>
           <div class="w-full h-full relative h-[250px]">'''

content = re.sub(dist_header_old, dist_header_new, content)

with open('desktop-app/src/index.html', 'w', encoding='utf-8') as f:
    f.write(content)

