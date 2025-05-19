const schema = JSON.parse(`{{fields|tojson|safe}}`);
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

    // Also enable/disable inputs
    const inputs = content.querySelectorAll("input, select, textarea");
    inputs.forEach((input) => {
      input.disabled = !checkbox.checked;
    });
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
  deleteButton.onclick = () => {
    rowContainer.remove();
    reindexArrayItems(containerId);
  };
  rowContainer.appendChild(input);
  rowContainer.appendChild(deleteButton);
  container.appendChild(rowContainer);
}

function reindexArrayItems(containerId) {
  const container = document.getElementById(containerId);
  const items = container.children;

  // Update the index for each remaining item
  Array.from(items).forEach((item, newIndex) => {
    const input = item.querySelector("input");
    if (input) {
      const oldName = input.name;
      const baseName = oldName.split("[")[0];
      input.name = `${baseName}[${newIndex}]`;
    }
  });
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
  if (fieldName === "id" && typeof isUpdate === "undefined") {
    return;
  }

  // Hide ID field in update mode
  if (fieldName === "_id" && isUpdate) {
    const inputWrapper = document.createElement("div");
    inputWrapper.className = "space-y-2";
    inputWrapper.style.display = "none"; // Hide the entire wrapper

    inputWrapper.innerHTML = `
      <label class="block">
        <span class="text-sm font-medium">ID</span>
        <input type="text" name="_id" readonly
               class="w-full mt-1 p-2 bg-slate-900 rounded text-gray-300">
      </label>
    `;

    container.appendChild(inputWrapper);
    return;
  }

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
    "flex  gap-2 items-start space-x-4 py-4 pl-3 border pr-2 bg-gray-800/80 border-gray-500 rounded-lg";

  const itemContent = document.createElement("div");
  itemContent.className = "flex-grow flex flex-col gap-8 w-full";

  createObjectInputs(itemSchema, itemContent, `${arrayName}[${rowIndex}]`);

  const deleteButton = document.createElement("button");
  deleteButton.className = "bg-red-600 m-1 p-1 min-w-8 min-h-8 rounded text-sm";
  deleteButton.textContent = "X";
  deleteButton.onclick = () => {
    rowContainer.remove();
    reindexComplexArrayItems(containerId);
  };
  rowContainer.appendChild(itemContent);
  rowContainer.appendChild(deleteButton);
  container.appendChild(rowContainer);
}
function reindexComplexArrayItems(containerId) {
  const container = document.getElementById(containerId);
  const items = container.children;

  Array.from(items).forEach((item, newIndex) => {
    const inputs = item.querySelectorAll("input, select, textarea");
    inputs.forEach((input) => {
      const oldName = input.name;
      const fieldPart = oldName.split("]")[1]; // Get the part after the index
      const baseName = oldName.split("[")[0];
      input.name = `${baseName}[${newIndex}]${fieldPart || ""}`;
    });
  });
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
  console.log("Populating form with data:", data);

  // Handle simple fields first
  Object.entries(data).forEach(([key, value]) => {
    const input = document.querySelector(`[name="${key}"]`);
    if (input) {
      if (input.type === "checkbox") {
        input.checked = Boolean(value);
      } else {
        input.value = value !== null ? value : "";
      }
    }
  });

  // Special case for the `_id` field
  // Find the ID input field
  const idInput = document.querySelector(`[name="_id"]`);
  if (idInput) {
    // If we're in update mode and have an ID, set the value
    if (data && data.id) {
      idInput.value = data.id;
    }

    // Hide the input itself
    idInput.style.display = "none";

    // Also hide the parent container (which likely contains the label)
    const parentContainer =
      idInput.closest(".form-group") || idInput.parentElement;
    if (parentContainer) {
      parentContainer.style.display = "none";
    }

    // Keep the field in the form data by making it readonly but not disabled
    idInput.setAttribute("readonly", true);
  }

  // Handle nested objects and arrays
  populateNestedData(data);
}

function populateNestedData(data, prefix = "") {
  Object.entries(data).forEach(([key, value]) => {
    const fullPath = prefix ? `${prefix}.${key}` : key;

    // Handle arrays
    if (Array.isArray(value)) {
      // Find the array container
      const containerID = `${fullPath}-container`;
      const container = document.getElementById(containerID);

      if (container) {
        // Ensure toggle is checked for this array if it exists
        const toggle = document.getElementById(`${fullPath}_toggle`);
        if (toggle) {
          toggle.checked = true;
          toggleArrayVisibility(toggle, containerID);
        }

        // Clear any existing items
        container.innerHTML = "";

        // Recreate each array item
        value.forEach((item, index) => {
          if (typeof item === "object" && item !== null) {
            // Complex object in array
            const itemType = determineItemType(item);
            if (itemType) {
              addArrayRow(fullPath, itemType, containerID);

              // After adding the row, populate its fields
              // The new row should be the last child of the container
              const newRow = container.lastElementChild;
              if (newRow) {
                // Find all inputs in this row and set their values
                Object.entries(item).forEach(([itemKey, itemValue]) => {
                  const itemPath = `${fullPath}[${index}].${itemKey}`;
                  populateItemField(newRow, itemPath, itemValue);
                });
              }
            }
          } else {
            // Simple value in array
            addSimpleArrayRow(fullPath, containerID);
            // Get the last added row and set its value
            const rowInput = container.lastElementChild.querySelector("input");
            if (rowInput) {
              rowInput.value = item;
            }
          }
        });
      }
    }
    // Handle nested objects
    else if (typeof value === "object" && value !== null) {
      // Find the content container for this object
      const contentId = `${fullPath}_content`;
      const content = document.getElementById(contentId);

      if (content) {
        // Enable the toggle if it exists
        const toggle = document.getElementById(`${fullPath}_toggle`);
        if (toggle) {
          toggle.checked = true;
          // Manually enable all fields in this container
          const inputs = content.querySelectorAll("input, select, textarea");
          inputs.forEach((input) => {
            input.disabled = false;
          });
        }

        // Populate the fields in this object
        Object.entries(value).forEach(([nestedKey, nestedValue]) => {
          const nestedPath = `${fullPath}.${nestedKey}`;
          populateItemField(content, nestedPath, nestedValue);
        });
      }
    }
  });
}

function populateItemField(container, fieldPath, value) {
  const input = container.querySelector(`[name="${fieldPath}"]`);
  if (input) {
    if (input.type === "checkbox") {
      input.checked = Boolean(value);
    } else {
      input.value = value !== null ? value : "";
    }
  }
}

function determineItemType(item) {
  // Try to match the item structure with schema definitions
  for (const [typeName, typeSchema] of Object.entries(schema.$)) {
    if (typeSchema && typeSchema.fields) {
      const fieldNames = Object.keys(typeSchema.fields);
      // If most of the item keys match the schema fields, assume it's this type
      const matchingFields = fieldNames.filter((field) => field in item);
      if (
        matchingFields.length > 0 &&
        matchingFields.length / fieldNames.length >= 0.5
      ) {
        return typeName;
      }
    }
  }
  return null;
}

document
  .getElementById(isUpdate ? "updateForm" : "createForm")
  .addEventListener("submit", async (e) => {
    e.preventDefault();

    // Create an object to hold our updated data
    const updatedData = {};

    // Extract the current form values
    const formData = new FormData(e.target);

    // Debug log
    console.log("Form data entries:");
    for (let [key, value] of formData.entries()) {
      console.log(`FormData Key: ${key}, Value: ${value}`);
    }

    // Process each form field
    for (let [key, value] of formData.entries()) {
      // Skip disabled fields (they won't be included in FormData anyway)
      const field = e.target.querySelector(`[name="${key}"]`);
      if (field && field.disabled) continue;

      // Parse the key to handle nested structures
      const parts = key.split(/[\[\].]/).filter(Boolean);

      // Start at the root of our data object
      let current = updatedData;

      // Build the nested structure
      for (let i = 0; i < parts.length; i++) {
        const part = parts[i];

        if (i === parts.length - 1) {
          // We're at the leaf node, set the actual value

          // Handle boolean values from checkboxes
          if (field && field.type === "checkbox") {
            value = field.checked;
          }
          // Convert string "true"/"false" to boolean
          else if (value === "true" || value === "false") {
            value = value === "true";
          }
          // Convert numeric strings to numbers
          else if (!isNaN(value) && value !== "") {
            value = Number(value);
          }

          // Set the value in our data structure
          current[part] = value;
        } else {
          // We're building the nested structure

          // Check if the next part is a number (array index)
          if (/^\d+$/.test(parts[i + 1])) {
            // Create array if it doesn't exist
            current[part] = current[part] || [];
          } else {
            // Create object if it doesn't exist
            current[part] = current[part] || {};
          }

          // Move deeper into the structure
          current = current[part];
        }
      }
    }

    // Process unchecked checkboxes (they don't appear in FormData)
    const allCheckboxes = e.target.querySelectorAll('input[type="checkbox"]');
    allCheckboxes.forEach((checkbox) => {
      if (checkbox.disabled) return; // Skip disabled checkboxes

      const name = checkbox.name;
      const parts = name.split(/[\[\].]/).filter(Boolean);

      // Check if this checkbox's value is already in updatedData
      // If not, it means it was unchecked
      let current = updatedData;
      let exists = true;

      for (let i = 0; i < parts.length - 1; i++) {
        if (!current[parts[i]]) {
          exists = false;
          break;
        }
        current = current[parts[i]];
      }

      const lastPart = parts[parts.length - 1];
      if (exists && !(lastPart in current)) {
        current[lastPart] = false;
      }
    });

    // Copy over the ID field to ensure it's included
    if (isUpdate && data && data.id) {
      updatedData.id = data.id;
    }

    try {
      const response = await fetch(window.location.pathname, {
        method: isUpdate ? "PUT" : "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(updatedData),
      });

      if (response.ok) {
        const result = await response.json();
        console.log("Success:", result);
        showToast(
          "Success",
          `Your data has been ${
            isUpdate ? "updated" : "submitted"
          } successfully!`,
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
  container.className = "fixed top-4 left-4 z-50 space-y-4";
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
    const response = await fetch(window.location.pathname, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
      },
    });

    if (response.ok) {
      console.log("Record deleted successfully.");
      showToast("Success", "Record deleted successfully!", "success");
      const currentUrl = window.location.pathname;
      const urlParts = currentUrl.split("/").filter((part) => part !== "");
      urlParts.pop();
      const redirectUrl = "/" + urlParts.join("/") + "/";

      console.log("Redirecting to:", redirectUrl);

      setTimeout(() => {
        window.location.href = redirectUrl;
      }, 2000);
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

// Form Update Real-Time Logger and Debugger

// Create a logging container
function createLogContainer() {
  const existingContainer = document.getElementById("formDataLogger");
  if (existingContainer) return existingContainer;

  const logContainer = document.createElement("div");
  logContainer.id = "formDataLogger";
  logContainer.className =
    "fixed bottom-4 right-4 w-96 max-h-96 bg-gray-800 border border-gray-600 rounded-lg shadow-lg p-3 overflow-y-auto z-50";
  logContainer.style.maxHeight = "400px";

  logContainer.innerHTML = `
    <div class="flex justify-between items-center mb-2 pb-2 border-b border-gray-600">
      <h3 class="text-sm font-bold text-white">Form Data Logger</h3>
      <div class="flex gap-2">
        <button id="captureFormState" class="text-xs bg-blue-600 px-2 py-1 rounded hover:bg-blue-700">Capture State</button>
        <button id="clearLogBtn" class="text-xs bg-gray-700 px-2 py-1 rounded hover:bg-gray-600">Clear</button>
        <button id="toggleLogBtn" class="text-xs bg-gray-700 px-2 py-1 rounded hover:bg-gray-600">Hide</button>
      </div>
    </div>
    <div id="logEntries" class="space-y-2 text-xs"></div>
  `;

  document.body.appendChild(logContainer);

  // Add button event listeners
  document.getElementById("clearLogBtn").addEventListener("click", () => {
    document.getElementById("logEntries").innerHTML = "";
  });

  document.getElementById("toggleLogBtn").addEventListener("click", (e) => {
    const logEntries = document.getElementById("logEntries");
    if (logEntries.style.display === "none") {
      logEntries.style.display = "block";
      e.target.textContent = "Hide";
    } else {
      logEntries.style.display = "none";
      e.target.textContent = "Show";
    }
  });

  document.getElementById("captureFormState").addEventListener("click", () => {
    const currentState = captureFormState();
    logMessage("Form State Snapshot", currentState, "snapshot");
    console.log("Current Form State:", currentState);
  });

  return logContainer;
}

// Capture current form state (all fields)
function captureFormState() {
  const form = document.getElementById(isUpdate ? "updateForm" : "createForm");
  if (!form) return null;

  const formState = {};

  // Get all input elements
  const inputs = form.querySelectorAll("input, select, textarea");
  inputs.forEach((input) => {
    if (!input.name) return;

    // Skip disabled inputs if we want to capture only enabled fields
    // if (input.disabled) return;

    if (input.type === "checkbox") {
      formState[input.name] = input.checked;
    } else {
      formState[input.name] = input.value;
    }
  });

  // Process the form data into a nested structure
  const structuredData = {};

  Object.entries(formState).forEach(([key, value]) => {
    // Parse the key to handle nested structures
    const parts = key.split(/[\[\].]/).filter(Boolean);

    // Start at the root of our data object
    let current = structuredData;

    // Build the nested structure
    for (let i = 0; i < parts.length; i++) {
      const part = parts[i];

      if (i === parts.length - 1) {
        // We're at the leaf node, set the actual value

        // Handle special value conversions
        if (typeof value === "string") {
          if (value === "true" || value === "false") {
            value = value === "true";
          } else if (!isNaN(value) && value !== "") {
            value = Number(value);
          }
        }

        // Set the value in our data structure
        current[part] = value;
      } else {
        // We're building the nested structure

        // Check if the next part is a number (array index)
        if (/^\d+$/.test(parts[i + 1])) {
          // Create array if it doesn't exist
          current[part] = current[part] || [];
        } else {
          // Create object if it doesn't exist
          current[part] = current[part] || {};
        }

        // Move deeper into the structure
        current = current[part];
      }
    }
  });

  return structuredData;
}

// Log a message to the log container
function logMessage(title, data, type = "info") {
  const logEntries = document.getElementById("logEntries");
  if (!logEntries) return;

  const timestamp = new Date().toLocaleTimeString();
  const logEntry = document.createElement("div");

  // Different styling based on type
  if (type === "error") {
    logEntry.className = "p-2 rounded bg-red-900/50 border-l-4 border-red-600";
  } else if (type === "warning") {
    logEntry.className =
      "p-2 rounded bg-yellow-900/50 border-l-4 border-yellow-600";
  } else if (type === "success") {
    logEntry.className =
      "p-2 rounded bg-green-900/50 border-l-4 border-green-600";
  } else if (type === "snapshot") {
    logEntry.className =
      "p-2 rounded bg-blue-900/50 border-l-4 border-blue-600";
  } else {
    logEntry.className = "p-2 rounded bg-gray-800 border border-gray-700";
  }

  // Format data object to string
  let dataHtml = "";
  if (data === null || data === undefined) {
    dataHtml = '<span class="text-gray-400">null or undefined</span>';
  } else if (typeof data === "object") {
    try {
      const jsonStr = JSON.stringify(data, null, 2);
      if (jsonStr === "{}") {
        dataHtml = '<span class="text-orange-400">Empty object {}</span>';
      } else {
        dataHtml = `<pre class="text-xs mt-1 p-2 bg-gray-900 rounded overflow-x-auto">${escapeHtml(
          jsonStr
        )}</pre>`;
      }
    } catch (e) {
      dataHtml = `<span class="text-red-400">Error stringifying: ${e.message}</span>`;
    }
  } else {
    dataHtml = `<span>${escapeHtml(String(data))}</span>`;
  }

  logEntry.innerHTML = `
    <div class="flex justify-between">
      <span class="font-medium text-white">${escapeHtml(title)}</span>
      <span class="text-gray-400 text-xs">${timestamp}</span>
    </div>
    <div class="mt-1">${dataHtml}</div>
  `;

  logEntries.prepend(logEntry);

  // Limit the number of log entries
  const maxEntries = 50;
  while (logEntries.children.length > maxEntries) {
    logEntries.removeChild(logEntries.lastChild);
  }
}

// Escape HTML to prevent XSS
function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

// Monitor form element changes
function attachFormMonitors() {
  const form = document.getElementById(isUpdate ? "updateForm" : "createForm");
  if (!form) {
    logMessage(
      "Form not found",
      `Could not find form with ID: ${isUpdate ? "updateForm" : "createForm"}`,
      "error"
    );
    return;
  }

  // Monitor input changes
  form.addEventListener("input", (e) => {
    if (!e.target.name) return;

    const fieldName = e.target.name;
    const newValue =
      e.target.type === "checkbox" ? e.target.checked : e.target.value;

    logMessage(`Field Changed: ${fieldName}`, { value: newValue }, "info");
  });

  // Monitor checkbox toggles
  form.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
    if (checkbox.id && checkbox.id.includes("_toggle")) {
      checkbox.addEventListener("change", () => {
        const targetId = checkbox.id.replace("_toggle", "_content");
        logMessage(`Toggle Section: ${targetId}`, {
          checked: checkbox.checked,
          visible: checkbox.checked,
        });
      });
    }
  });

  // Intercept form submission
  const originalSubmit = form.onsubmit;
  form.onsubmit = async function (e) {
    e.preventDefault();

    logMessage(
      "Form Submission Started",
      {
        time: new Date().toISOString(),
        isUpdate: isUpdate || false,
      },
      "info"
    );

    // Capture and log the complete form state
    const formState = captureFormState();
    logMessage(
      "Form Submission Data",
      formState,
      formState && Object.keys(formState).length ? "success" : "warning"
    );

    // Collect FormData entries for debugging
    const formData = new FormData(form);
    const formDataEntries = {};
    for (let [key, value] of formData.entries()) {
      formDataEntries[key] = value;
    }

    logMessage("Raw FormData Entries", formDataEntries);

    // Check for empty submission
    if (!formState || Object.keys(formState).length === 0) {
      logMessage(
        "Empty Form Submission",
        "The form data is empty! Check for form field naming issues.",
        "error"
      );
    }

    // Call the original submit handler if it exists
    if (originalSubmit) {
      return originalSubmit.call(this, e);
    }
  };

  // Override the existing updateData function if it exists
  if (typeof window.updateData === "function") {
    const originalUpdateData = window.updateData;
    window.updateData = function (data) {
      logMessage("updateData Called", data, "info");
      return originalUpdateData.apply(this, arguments);
    };
  }

  // Override the populateFormWithExistingData function
  if (typeof window.populateFormWithExistingData === "function") {
    const originalPopulate = window.populateFormWithExistingData;
    window.populateFormWithExistingData = function (data) {
      logMessage("Populating Form with Data", data, data ? "info" : "warning");

      if (!data || Object.keys(data).length === 0) {
        logMessage(
          "Empty Data for Form Population",
          "This might explain missing form values",
          "warning"
        );
      }

      // Call original function
      const result = originalPopulate.apply(this, arguments);

      // Capture the form state after population
      setTimeout(() => {
        const formState = captureFormState();
        logMessage("Form State After Population", formState, "snapshot");

        // Check if fields are disabled when they shouldn't be
        const disabledInputs = form.querySelectorAll(
          "input:disabled, select:disabled, textarea:disabled"
        );
        if (disabledInputs.length > 0) {
          const disabledFields = Array.from(disabledInputs)
            .map((el) => el.name)
            .filter(Boolean);
          if (disabledFields.length > 0) {
            logMessage("Found Disabled Fields", disabledFields, "warning");
          }
        }
      }, 100);

      return result;
    };
  }

  // Debug the fetch call
  const originalFetch = window.fetch;
  window.fetch = function (...args) {
    const [url, options] = args;

    if (
      options &&
      options.method &&
      (options.method === "POST" || options.method === "PUT")
    ) {
      logMessage(
        `Fetch Request (${options.method})`,
        {
          url: url,
          method: options.method,
          bodyData: options.body ? JSON.parse(options.body) : null,
        },
        "info"
      );
    }

    const fetchPromise = originalFetch.apply(this, args);

    fetchPromise
      .then((response) => {
        if (!response.ok) {
          logMessage(
            "Fetch Error",
            {
              status: response.status,
              statusText: response.statusText,
            },
            "error"
          );
        } else {
          logMessage(
            "Fetch Success",
            {
              status: response.status,
            },
            "success"
          );
        }
      })
      .catch((error) => {
        logMessage(
          "Fetch Failed",
          {
            error: error.message,
          },
          "error"
        );
      });

    return fetchPromise;
  };
}

// Initialize the logger
function initFormLogger() {
  createLogContainer();
  attachFormMonitors();

  // Log initial system state
  logMessage(
    "Form Logger Initialized",
    {
      url: window.location.href,
      isUpdate: typeof isUpdate !== "undefined" ? isUpdate : false,
      time: new Date().toISOString(),
    },
    "info"
  );

  // Check if existingData is available
  if (typeof existingData !== "undefined") {
    logMessage(
      "Existing Data Found",
      existingData,
      existingData ? "info" : "warning"
    );
  } else {
    logMessage("No Existing Data", "existingData is not defined", "warning");
  }

  // Log initial schema
  if (typeof schema !== "undefined") {
    logMessage("Schema Structure", {
      hasFields: schema.fields ? true : false,
      nestedTypes: schema.$ ? Object.keys(schema.$) : [],
    });
  }

  // Check form action is correctly set
  setTimeout(() => {
    const form = document.getElementById(
      isUpdate ? "updateForm" : "createForm"
    );
    if (form) {
      logMessage("Form Configuration", {
        action: form.action || window.location.pathname,
        method: form.method || "POST/PUT via JS",
        id: form.id,
        containsInputs:
          form.querySelectorAll("input, select, textarea").length > 0,
      });
    }
  }, 500);
}

// Run on page load
document.addEventListener("DOMContentLoaded", function () {
  setTimeout(initFormLogger, 100); // Slight delay to ensure page is fully loaded
});

// For immediate execution if the page is already loaded
if (
  document.readyState === "complete" ||
  document.readyState === "interactive"
) {
  setTimeout(initFormLogger, 100);
}
