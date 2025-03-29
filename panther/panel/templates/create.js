const schema = JSON.parse(`{{fields|tojson|safe}}`);
console.log(schema);
function toggleObjectVisibility(checkbox, contentId) {
  const content = document.getElementById(contentId);
  content.classList.toggle("hidden", !checkbox.checked);

  // Disable/enable all inputs within the container
  const inputs = content.querySelectorAll("input, select, textarea");
  inputs.forEach((input) => {
    input.disabled = !checkbox.checked;
  });
}

function createObjectInputs(objectSchema, container, prefix = "") {
  if (!objectSchema || !objectSchema.fields) return;

  Object.entries(objectSchema.fields).forEach(([fieldName, field]) => {
    const fullFieldName = prefix ? `${prefix}.${fieldName}` : fieldName;

    // Check if it's an array type
    if (field.type.includes("array")) {
      // If items is specified, use it
      if (field.items) {
        const itemType = field.items.replace("$", "");
        createArrayField(fieldName, itemType, container, fullFieldName, field);
      } else {
        // Handle array without items specification (simple types)
        createSimpleArrayField(fieldName, container, fullFieldName, field);
      }
    } else if (
      Array.isArray(field.type) &&
      field.type.some((t) => t.startsWith("$"))
    ) {
      const objectType = field.type
        .find((t) => t.startsWith("$"))
        .replace("$", "");
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
    content.classList.toggle("hidden", !checkbox.checked);
  }
}

function createSimpleArrayField(fieldName, container, fullFieldName, field) {
  const arrayContainer = document.createElement("div");
  arrayContainer.className = "border border-gray-400 p-4 rounded-lg space-y-2";

  const spreadsheetId = `${fullFieldName}-container`;

  const header = document.createElement("div");
  header.className = "flex items-center justify-between mb-4";
  header.innerHTML = `
    <h3 class="text-lg font-medium">${field.title || fieldName}</h3>
    ${
      field.type.includes("null")
        ? `
      <label class="flex items-center space-x-3">
        <input type="checkbox" 
               id="${fullFieldName}_toggle"
               class="form-checkbox h-5 w-5 text-blue-600 bg-gray-700 border-gray-600 rounded"
               ${!field.required ? "" : "checked disabled"}
               onchange="toggleArrayVisibility(this, '${spreadsheetId}')">
        <span class="text-sm font-medium">Include ${
          field.title || fieldName
        }</span>
      </label>
    `
        : ""
    }
  `;

  const content = document.createElement("div");
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

  if (field.type.includes("null") && !field.required) {
    content.classList.add("hidden");
  }

  arrayContainer.appendChild(header);
  arrayContainer.appendChild(content);
  container.appendChild(arrayContainer);
}

function addSimpleArrayRow(arrayName, containerId) {
  const container = document.getElementById(containerId);
  if (!container) {
    console.error("Invalid container");
    return;
  }

  const rowIndex = container.children.length;
  const rowContainer = document.createElement("div");
  rowContainer.className = "flex items-center space-x-4";

  const input = document.createElement("input");
  input.type = "text";
  input.name = `${arrayName}[${rowIndex}]`;
  input.className =
    "flex-grow bg-gray-700 border border-gray-600 rounded px-3 py-2";

  const deleteButton = document.createElement("button");
  deleteButton.className = "bg-red-600 px-3 py-1 rounded text-sm";
  deleteButton.textContent = "Delete";
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
  const objectWrapper = document.createElement("div");
  objectWrapper.className = "space-y-4 border border-gray-400 p-4 rounded-lg";

  const cleanObjectType = objectType.replace(/^\$/, "");

  const header = document.createElement("div");
  header.className = "flex items-center justify-between mb-4";
  header.innerHTML = `<h3 class="text-lg font-medium">${
    field.title || fieldName
  }</h3>`;

  const contentContainer = document.createElement("div");
  contentContainer.id = `${fullFieldName}_content`;
  contentContainer.className = "space-y-4";

  // Add toggle for optional objects
  if (!field.required) {
    const toggleContainer = document.createElement("div");
    toggleContainer.className = "flex items-center space-x-3";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.id = `${fullFieldName}_toggle`;
    checkbox.className = "form-checkbox h-5 w-5 text-blue-600";

    const label = document.createElement("label");
    label.htmlFor = `${fullFieldName}_toggle`;
    label.textContent = `Include ${field.title || fieldName}`;

    toggleContainer.appendChild(checkbox);
    toggleContainer.appendChild(label);
    header.appendChild(toggleContainer);

    // Toggle handler to enable/disable validation
    checkbox.addEventListener("change", (e) => {
      const fields = contentContainer.querySelectorAll(
        "input, select, textarea"
      );
      fields.forEach((field) => {
        if (!e.target.checked) {
          // When unchecked, disable and remove required attribute
          field.disabled = true;
          field.required = false;
          field.value = ""; // Clear the value
        } else {
          // When checked, enable and restore required if it was originally required
          field.disabled = false;
          field.required = field.dataset.originalRequired === "true";
        }
      });
    });

    // Initialize as unchecked
    checkbox.checked = false;
    setTimeout(() => checkbox.dispatchEvent(new Event("change")), 0);
  }

  const nestedSchema = schema.$[cleanObjectType];
  createObjectInputs(nestedSchema, contentContainer, fullFieldName);

  // Store original required state for all nested fields
  contentContainer
    .querySelectorAll("input, select, textarea")
    .forEach((field) => {
      field.dataset.originalRequired = field.required;
      if (!field.required) {
        field.required = false;
      }
    });

  objectWrapper.appendChild(header);
  objectWrapper.appendChild(contentContainer);
  container.appendChild(objectWrapper);
}

function createObjectInputs(objectSchema, container, prefix = "") {
  if (!objectSchema || !objectSchema.fields) return;

  Object.entries(objectSchema.fields).forEach(([fieldName, field]) => {
    const fullFieldName = prefix ? `${prefix}.${fieldName}` : fieldName;

    // Check if it's an array type
    if (field.type.includes("array")) {
      // If items is specified, use it
      if (field.items) {
        const itemType = field.items.replace("$", "");
        createArrayField(fieldName, itemType, container, fullFieldName, field);
      } else {
        // Handle array without items specification (simple types)
        createSimpleArrayField(fieldName, container, fullFieldName, field);
      }
    } else if (
      // Check if type is an array and contains a reference to another type
      (Array.isArray(field.type) &&
        field.type.some((t) => t.startsWith("$"))) ||
      // Or if type is a string and is a reference
      (typeof field.type === "string" && field.type.startsWith("$"))
    ) {
      const objectType = Array.isArray(field.type)
        ? field.type.find((t) => t.startsWith("$"))
        : field.type;
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

function createBasicInput(fieldName, field, container, fullFieldName) {
  const inputWrapper = document.createElement("div");
  inputWrapper.className = "space-y-2";

  let inputHTML = "";
  const defaultValue =
    field.default !== undefined ? `value="${field.default}"` : "";
  const requiredText = field.required
    ? `<span class="text-red-500 text-sm ml-2">* Required</span>`
    : "";

  if (field.type.includes("boolean")) {
    inputHTML = `
        <label class="flex items-center space-x-3">
          <input type="checkbox" name="${fullFieldName}"
                 ${field.default ? "checked" : ""}
                 class="form-checkbox h-5 w-5 text-blue-600 bg-gray-700 border-gray-600 rounded">
          <span class="text-sm font-medium">${field.title || fieldName}</span>
          ${requiredText}
        </label>
      `;
  } else if (field.type.includes("string")) {
    inputHTML = `
      <label class="block">
        <span class="text-sm font-medium">${
          field.title || fieldName
        } ${requiredText}</span>
        <input type="text" name="${fullFieldName}"
               ${defaultValue}
               ${field.required ? "required" : ""}
               class="w-full mt-1 p-2 bg-slate-900 rounded text-gray-300">
      </label>
    `;
  } else if (field.type.includes("integer")) {
    const min = field.min !== undefined ? `min="${field.min}"` : "";
    const max = field.max !== undefined ? `max="${field.max}"` : "";

    inputHTML = `
      <label class="block">
        <span class="text-sm font-medium">${
          field.title || fieldName
        } ${requiredText}</span>
        <input type="number" name="${fullFieldName}"
               ${defaultValue} ${min} ${max}
               ${field.required ? "required" : ""}
               class="w-full mt-1 p-2 bg-slate-900 rounded text-gray-300">
      </label>
    `;
  }

  inputWrapper.innerHTML = inputHTML;
  container.appendChild(inputWrapper);
}

function createArrayField(fieldName, itemType, container, fullFieldName) {
  const arrayContainer = document.createElement("div");
  arrayContainer.className = "border border-gray-700 p-4 rounded-lg space-y-4";

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
    console.error("Invalid container or schema type");
    return;
  }

  const itemSchema = schema.$[itemType];
  const rowIndex = container.children.length;
  const rowContainer = document.createElement("div");
  rowContainer.className =
    "flex  gap-2 items-start space-x-4 py-2 pl-2 pr-1 bg-gray-700/50 rounded-lg";

  const itemContent = document.createElement("div");
  itemContent.className = "flex-grow flex flex-col gap-8 w-full";

  createObjectInputs(itemSchema, itemContent, `${arrayName}[${rowIndex}]`);

  const deleteButton = document.createElement("button");
  deleteButton.className = "bg-red-600 m-1 p-1 min-w-8 min-h-8 rounded text-sm";
  deleteButton.textContent = "X";
  deleteButton.onclick = () => rowContainer.remove();

  rowContainer.appendChild(itemContent);
  rowContainer.appendChild(deleteButton);
  container.appendChild(rowContainer);
}

function openObjectModal(fieldName, objectType) {
  // Create modal for editing nested object
  const modal = document.createElement("div");
  modal.className =
    "fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center";
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
    modal.querySelector(".object-inputs"),
    fieldName
  );

  document.body.appendChild(modal);
}

const dynamicInputs = document.getElementById("dynamicInputs");

createObjectInputs(schema, dynamicInputs);

// Check if the page is in update mode
if (typeof isUpdate !== "undefined" && isUpdate) {
  // Populate the form with existing data for update mode
  populateFormWithExistingData(existingData);
} else {
  console.log("Create mode: No existing data to populate.");
}

// Function to populate the form with existing data
function populateFormWithExistingData(data) {
  const dynamicInputs = document.getElementById("dynamicInputs");
  if (!dynamicInputs) return;

  // Iterate over the existing data and pre-fill the inputs
  Object.entries(data).forEach(([key, value]) => {
    // Find the input field by its name attribute
    const input = dynamicInputs.querySelector(`[name="${key}"]`);
    if (input) {
      if (input.type === "checkbox") {
        input.checked = Boolean(value);
      } else {
        input.value = value !== null ? value : ""; // Set the value or leave it empty
      }
    }
  });

  // Special case for the `_id` field if it doesn't match the key in the data
  const idInput = dynamicInputs.querySelector(`[name="_id"]`);
  if (idInput && data.id) {
    idInput.value = data.id; // Map the `id` field to the `_id` input
  }
}

// Modify the form submission logic to handle both create and update
document.getElementById(isUpdate ? "updateForm" : "createForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const formData = new FormData(e.target);

  for (let [key, value] of formData.entries()) {
    const parts = key.split(/[\[\].]/).filter(Boolean);
    let current = data;

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (i === parts.length - 1) {
        // Handle boolean values
        if (value === "true" || value === "false") {
          value = value === "true"; // Convert string to boolean
        }

        // Convert numeric strings to numbers
        else if (!isNaN(value) && value !== "") {
          value = Number(value);
        }

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

  // Explicitly set unchecked checkboxes to false for all boolean fields
  const allCheckboxes = e.target.querySelectorAll('input[type="checkbox"]');
  allCheckboxes.forEach((checkbox) => {
    const name = checkbox.name;
    const parts = name.split(/[\[\].]/).filter(Boolean);
    let current = data;

    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];
      if (i === parts.length - 1) {
        // Make sure checkbox values are always boolean
        if (!(part in current)) {
          current[part] = false;
        } else if (typeof current[part] === "string") {
          current[part] = current[part] === "true";
        }
      } else {
        if (/^\d+$/.test(parts[i + 1])) {
          current[part] = current[part] || [];
        } else {
          current[part] = current[part] || {};
        }
        current = current[part];
      }
    }
  });

  try {
    console.log("Data being sent:", data); // Debugging log
    const response = await fetch(isUpdate ? `/detail  /${data.id}` : "./", {
      method: isUpdate ? "PUT" : "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    if (response.ok) {
      const result = await response.json();
      console.log("Success:", result);
      showToast(
        "Success",
        `Your data has been ${isUpdate ? "updated" : "submitted"} successfully!`,
        "success"
      );
    } else {
      const errorText = await response.text();
      console.error("Error:", response.status, response.statusText);
      showToast("Error", `Error ${response.status}: ${errorText}`, "error");
    }
  } catch (error) {
    console.error("Fetch error:", error);
    showToast(
      "Error",
      "An unexpected error occurred. Please try again.",
      "error"
    );
  }
});

// Toast function
function showToast(title, message, type) {
  const toastContainer =
    document.getElementById("toastContainer") || createToastContainer();
  const toast = document.createElement("div");
  toast.className = `toast ${
    type === "success" ? "border-green-600" : "border-red-600"
  } p-4 mb-4 rounded shadow-lg bg-gray-900 text-gray-100 border-l-4 p-4 rounded-lg shadow-md animate-fadeIn`;
  toast.innerHTML = `
    <strong class="block text-lg">${title}</strong>
    <span class="block text-sm">${message}</span>
  `;
  toastContainer.appendChild(toast);

  // Automatically remove the toast after 5 seconds
  setTimeout(() => {
    toast.remove();
  }, 5000);
}

function createToastContainer() {
  const container = document.createElement("div");
  container.id = "toastContainer";
  container.className = "fixed top-4 right-4 z-50 space-y-4";
  document.body.appendChild(container);
  return container;
}

document.getElementById("deleteButton").addEventListener("click", async () => {
  if (!data.id) {
    console.error("No ID found for deletion.");
    showToast("Error", "No ID found for deletion.", "error");
    return;
  }

  const confirmDelete = confirm("Are you sure you want to delete this record?");
  if (!confirmDelete) return;

  try {
    const response = await fetch(`/${data.id}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      console.log("Record deleted successfully.");
      showToast("Success", "Record deleted successfully!", "success");

      // Optionally redirect or refresh the page
      setTimeout(() => {
        window.location.href = "/"; // Redirect to the homepage or another page
      }, 2000);
    } else {
      const errorText = await response.text();
      console.error("Error:", response.status, response.statusText);
      showToast("Error", `Error ${response.status}: ${errorText}`, "error");
    }
  } catch (error) {
    console.error("Fetch error:", error);
    showToast("Error", "An unexpected error occurred. Please try again.", "error");
  }
});
