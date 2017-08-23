function selectAll(className) {
  checkboxes = document.getElementsByName(className);
  for(var i in checkboxes) {
    checkboxes[i].checked = true;
  }
}

function deselectAll(className) {
  checkboxes = document.getElementsByName(className);
  for(var i in checkboxes) {
    checkboxes[i].checked = false;
  }
}

$("document").ready(function(){
  var file = document.getElementById("uploadID");

  document.getElementById("uploadID").onchange = function(){

    var table = document.getElementById("table");
    var matrix = {"0": ["limit","hence"]};
    uploadedfile = file.files
    var formdata = new FormData();
    formdata.append("file", uploadedfile[0])
    console.log('here', formdata)
    $.post("getImportfields", {data: formdata,
    contentType: false, processData: false,}, function( data ) {
      console.log(data)
      matrix = data

      var htmlDump = ''

      htmlDump += `
        <label> Specify fields to import </label>
        <h5> Defualt fields:{@type, path, id, UID}</h5>

        <!-- buttons for SelectAll and DeselectAll -->
        <div >
          <input type="button" onclick= "selectAll('importFields')"  value="Select all"
            name="Select"/>
          <input type="button" onclick="deselectAll('importFields')" value="Deselect all"
            name="Deselect"/>
        </div>
      `
      <!-- Dynamic Table -->
      htmlDump += "<table>";
      for (var i in Object.keys(matrix)){
        htmlDump += "<tr>";
        for (var j in matrix[i]){
          htmlDump += `
            <td>
            <input type="checkbox" name="importFields">
          `;
          <!-- TODO mention value in these fields -->
          htmlDump += matrix[i][j];
          htmlDump += `
            </input>
            </td>
          `;
        }
        htmlDump += "</tr>";
      }
      htmlDump += "</table>";


      htmlDump += `
        <label> Action to take if content already existed?</label>
        <br>

        <input type="radio" name="actionExist" value="update"
          checked="checked">
          Update
        </input>

        <input type="radio" name="actionExist" value="ignore" >
          Ignore
        </input>

        <input type="radio" name="actionExist" onclick="createNew()" value="new">
          Create New
        </input>

        <div id="createNew">
        </div>

        <br>
        <br>

        <input type="submit" name="imports" value="Import" i18n:attributes="value" />

      `
      table.innerHTML = htmlDump;
    });


  };
});

function createNew() {
  console.log("creating new")
  <!-- TODO define mechanism to dynamically generate table for create new -->
};
