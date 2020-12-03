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

require(['jquery'
], function($){

    $("document").ready(function(){

      var file = document.getElementById("uploadID");
      file.onchange = function(){

        var table = document.getElementById("table");
        uploadedfile = file.files;
        var formdata = new FormData();
        formdata.append('section', 'general');
        formdata.append('action', 'previewImg');

        for (var i = 0; i < uploadedfile.length ; i++) {
              formdata.append("file", uploadedfile[i]);
            }

        $.ajax({
          url: "getImportfields",
          data: formdata,
          type: 'POST',
          contentType: false,
          processData: false,
          success:  function (data) {
                      matrix = JSON.parse(data)
                      console.log(matrix)
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
                      htmlDump += "<table class='listing import_export_setting'>";
                      for (var i in Object.keys(matrix)){
                        htmlDump += "<tr>";
                        for (var j in matrix[i]){
                          htmlDump += `
                            <td>
                            <input type="checkbox" name="importFields" value="`;
                          htmlDump += matrix[i][j] + `">`
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

                        <!-- TODO Radio button for create new -->
                        <!-- <input type="radio" name="matching_content" onclick="createNew()" value="new">
                          Create New
                        </input> -->

                        <div id="createNew">
                        </div>

                        <br>
                        <br>

                        <input type="submit" name="imports" value="Import" i18n:attributes="value" />
                      `
                      // Error handling
                      if (Object.keys(matrix)[0]=='Error'){
                        htmlDump = matrix.toSource()
                      }
                      table.innerHTML = htmlDump;
                  }

        });


      };

    });

});

function createNew() {
  console.log("creating new")
  <!-- TODO define mechanism to dynamically generate table for create new -->
};
