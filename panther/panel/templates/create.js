const schema = JSON.parse('{{fields|tojson|safe}}');
console.log(schema);

function toggleObjectVisibility(checkbox, contentId) {
  const content = document.getElementById(contentId);
  content.classList.toggle('hidden', !checkbox.checked);

  // Disable/enable all inputs within the container
  const inputs = content.querySelectorAll('input, select, textarea');
  inputs.forEach((input) => {
    input.disabled = !checkbox.checked;
  });
}

function createObjectInputs(objectSchema, container, prefix = '') {
  if (!objectSchema || !objectSchema.fields) return;

  Object.entries(objectSchema.fields).forEach(([fieldName, field]) => {
    const fullFieldName = prefix ? `${prefix}.${fieldName}` : fieldName;

    // Check if it's an array type
    if (field.type.includes('array')) {
      // If items is specified, use it
      if (field.items) {
        const itemType = field.items.replace('$', '');
        createArrayField(fieldName, itemType, container, fullFieldName, field);
      } else {
        // Handle array without items specification (simple types)
        createSimpleArrayField(fieldName, container, fullFieldName, field);
      }
    } else if (
      Array.isArray(field.type) &&
      field.type.some((t) => t.startsWith('$'))
    ) {
      const objectType = field.type
        .find((t) => t.startsWith('$'))
        .replace('$', '');
      createNestedObjectField(
        fieldName,
        objectType,
        field,
        container,
        fullFieldName
      );
    } else {
      createBasicInput(fieldName, field, container, fullFieldName);
    }
  });
}

function toggleArrayVisibility(checkbox, contentId) {
  const content = document.getElementById(contentId);
  if (content) {
    content.classList.toggle('hidden', !checkbox.checked);
  }
}

function createSimpleArrayField(fieldName, container, fullFieldName, field) {
  const arrayContainer = document.createElement('div');
  arrayContainer.className = 'border border-gray-400 p-4 rounded-lg space-y-2';

  const spreadsheetId = `${fullFieldName}-container`;

  const header = document.createElement('div');
  header.className = 'flex items-center justify-between mb-4';
  header.innerHTML = `
    <h3 class="text-lg font-medium">${field.title || fieldName}</h3>
    ${
      field.type.includes('null')
        ? `
      <label class="flex items-center space-x-3">
        <input type="checkbox" 
               id="${fullFieldName}_toggle"
               class="form-checkbox h-5 w-5 text-blue-600 bg-gray-700 border-gray-600 rounded"
               ${!field.required ? '' : 'checked disabled'}
               onchange="toggleArrayVisibility(this, '${spreadsheetId}')">
        <span class="text-sm font-medium">Include ${
          field.title || fieldName
        }</span>
      </label>
    `
        : ''
    }
  `;

  const content = document.createElement('div');
  content.innerHTML = `
    <div class="flex justify-between items-center mb-4">
      <button type="button" 
              class="bg-green-600 px-3 py-1 rounded text-sm"
              onclick="addSimpleArrayRow('${fullFieldName}', '${spreadsheetId}')">
        Add Item
      </button>
    </div>
    <div id="${spreadsheetId}" class="array-items space-y-4">
    </div>
  `;

  if (field.type.includes('null') && !field.required) {
    content.classList.add('hidden');
  }

  arrayContainer.appendChild(header);
  arrayContainer.appendChild(content);
  container.appendChild(arrayContainer);
}

function addSimpleArrayRow(arrayName, containerId) {
  const container = document.getElementById(containerId);
  if (!container) {
    console.error('Invalid container');
    return;
  }

  const rowIndex = container.children.length;
  const rowContainer = document.createElement('div');
  rowContainer.className = 'flex items-center space-x-4';

  const input = document.createElement('input');
  input.type = 'text';
  input.name = `${arrayName}[${rowIndex}]`;
  input.className =
    'flex-grow bg-gray-700 border border-gray-600 rounded px-3 py-2';

  const deleteButton = document.createElement('button');
  deleteButton.className = 'bg-red-600 px-3 py-1 rounded text-sm';
  deleteButton.textContent = 'Delete';
  deleteButton.onclick = () => rowContainer.remove();

  rowContainer.appendChild(input);
  rowContainer.appendChild(deleteButton);
  container.appendChild(rowContainer);
}
function createNestedObjectField(
  fieldName,
  objectType,
  field,
  container,
  fullFieldName
) {
  const objectWrapper = document.createElement('div');
  objectWrapper.className = 'space-y-4 border border-gray-400 p-4 rounded-lg';

  // Check if the objectType exists in schema.$
  if (!schema.$ || !schema.$[objectType]) {
    console.error(`Schema type ${objectType} not found`);
    return;
  }

  const header = document.createElement('div');
  header.className = 'flex items-center justify-between mb-4';
  header.innerHTML = `
    <h3 class="text-lg font-medium">${field.title || fieldName}</h3>
    ${
      field.type.includes('null')
        ? `
      <label class="flex items-center space-x-3">
        <input type="checkbox" 
               id="${fullFieldName}_toggle"
               class="form-checkbox h-5 w-5 text-blue-600 bg-gray-700 border-gray-600 rounded"
               ${!field.required ? '' : 'checked disabled'}
               onchange="toggleObjectVisibility(this, '${fullFieldName}_content')">
        <span class="text-sm font-medium">Include ${
          field.title || fieldName
        }</span>
      </label>
    `
        : ''
    }
  `;

  const contentContainer = document.createElement('div');
  contentContainer.id = `${fullFieldName}_content`;
  contentContainer.className = 'space-y-4';

  if (field.type.includes('null') && !field.required) {
    contentContainer.classList.add('hidden');
  }

  const nestedSchema = schema.$[objectType];
  createObjectInputs(nestedSchema, contentContainer, fullFieldName);

  objectWrapper.appendChild(header);
  objectWrapper.appendChild(contentContainer);
  container.appendChild(objectWrapper);
}

function createBasicInput(fieldName, field, container, fullFieldName) {
  const inputWrapper = document.createElement('div');
  inputWrapper.className = 'space-y-2';

  let inputHTML = '';
  if (field.type.includes('boolean')) {
    inputHTML = `
                <label class="flex items-center space-x-3">
                    <input type="checkbox" name="${fullFieldName}"
                           ${field.required ? 'required' : ''}
                           class="form-checkbox h-5 w-5 text-blue-600 bg-gray-700 border-gray-600 rounded">
                    <span class="text-sm font-medium">${
                      field.title || fieldName
                    }</span>
                </label>
            `;
  } else if (field.type.includes('string')) {
    inputHTML = `
                <label class="block">
                    <span class="text-sm font-medium">${
                      field.title || fieldName
                    }</span>
                    <input type="text" name="${fullFieldName}"
                           ${field.required ? 'required' : ''}
                           class="w-full mt-1 p-2 bg-slate-900 rounded text-gray-300">
                </label>
            `;
  } else if (field.type.includes('integer')) {
    inputHTML = `
                <label class="block">
                    <span class="text-sm font-medium">${
                      field.title || fieldName
                    }</span>
                    <input type="number" name="${fullFieldName}"
                           ${field.required ? 'required' : ''}
                           class="w-full mt-1 p-2 bg-slate-900 rounded text-gray-300">
                </label>
            `;
  }

  inputWrapper.innerHTML = inputHTML;
  container.appendChild(inputWrapper);
}

function createArrayField(fieldName, itemType, container, fullFieldName) {
  const arrayContainer = document.createElement('div');
  arrayContainer.className = 'border border-gray-700 p-4 rounded-lg space-y-4';

  const spreadsheetId = `${fullFieldName}-container`;

  // Make sure itemType exists in schema.$
  if (!schema.$ || !schema.$[itemType]) {
    console.error(`Schema type ${itemType} not found`);
    return;
  }

  arrayContainer.innerHTML = `
    <div class="flex justify-between items-center mb-4">
      <h3 class="text-lg font-medium">${fieldName}</h3>
      <button type="button" 
              class="bg-green-600 px-3 py-1 rounded text-sm"
              onclick="addArrayRow('${fullFieldName}', '${itemType}', '${spreadsheetId}')">
        Add Item
      </button>
    </div>
    <div id="${spreadsheetId}" class="array-items space-y-4"></div>
  `;

  container.appendChild(arrayContainer);
}

function addArrayRow(arrayName, itemType, containerId) {
  const container = document.getElementById(containerId);
  if (!container || !schema.$ || !schema.$[itemType]) {
    console.error('Invalid container or schema type');
    return;
  }

  const itemSchema = schema.$[itemType];
  const rowIndex = container.children.length;

  const rowContainer = document.createElement('div');
  rowContainer.className =
    'flex  gap-2 items-start space-x-4 py-2 pl-2 pr-1 bg-gray-700/50 rounded-lg';

  const itemContent = document.createElement('div');
  itemContent.className = 'flex-grow flex flex-col gap-8 w-full';

  createObjectInputs(itemSchema, itemContent, `${arrayName}[${rowIndex}]`);

  const deleteButton = document.createElement('button');
  deleteButton.className = 'bg-red-600 m-1 p-1 min-w-8 min-h-8 rounded text-sm';
  deleteButton.textContent = 'X';
  deleteButton.onclick = () => rowContainer.remove();

  rowContainer.appendChild(itemContent);
  rowContainer.appendChild(deleteButton);
  container.appendChild(rowContainer);
}

function openObjectModal(fieldName, objectType) {
  // Create modal for editing nested object
  const modal = document.createElement('div');
  modal.className =
    'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center';
  modal.innerHTML = `
<div class="bg-gray-800 p-6 rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
  <h3 class="text-lg font-medium mb-4">Edit ${fieldName}</h3>
  <div class="object-inputs space-y-4"></div>
  <div class="mt-4 flex justify-end space-x-2">
    <button type="button" class="bg-gray-600 px-4 py-2 rounded" onclick="this.closest('.fixed').remove()">
      Cancel
    </button>
    <button type="button" class="bg-blue-600 px-4 py-2 rounded" onclick="saveObjectModal(this)">
      Save
    </button>
  </div>
</div>
`;

  const objectSchema = schema.$[objectType];
  createObjectInputs(
    objectSchema,
    modal.querySelector('.object-inputs'),
    fieldName
  );

  document.body.appendChild(modal);
}

const dynamicInputs = document.getElementById('dynamicInputs');

createObjectInputs(schema, dynamicInputs);

document.getElementById('createForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);
  const data = {};

  for (let [key, value] of formData.entries()) {
    const parts = key.split(/[\[\].]/).filter(Boolean);
    let current = data;

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (i === parts.length - 1) {
        // Convert values to appropriate types
        if (value === 'on') value = true;
        if (value === 'off') value = false;
        if (!isNaN(value) && value !== '') value = Number(value);
        current[part] = value;
      } else {
        if (/^\d+$/.test(parts[i + 1])) {
          current[part] = current[part] || [];
        } else {
          current[part] = current[part] || {};
        }
        current = current[part];
      }
    }
  }

  try {
    const response = await fetch('./', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (response.ok) {
      const result = await response.json();
      console.log('Success:', result);
    } else {
      console.error('Error:', response.status, response.statusText);
    }
  } catch (error) {
    console.error('Fetch error:', error);
  }
});
